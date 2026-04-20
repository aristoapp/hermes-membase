from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable

import httpx

DEFAULT_TIMEOUT_S = 15.0
TokenRefreshCallback = Callable[[str, str], None]


class MembaseApiError(RuntimeError):
    def __init__(self, message: str, status: int, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


@dataclass
class AuthState:
    access_token: str
    refresh_token: str
    client_id: str


class MembaseClient:
    def __init__(
        self,
        api_url: str,
        auth: AuthState,
        *,
        source: str = "hermes",
        timeout_s: float = DEFAULT_TIMEOUT_S,
        debug: bool = False,
        logger: logging.Logger | None = None,
        on_token_refresh: TokenRefreshCallback | None = None,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.access_token = auth.access_token
        self.refresh_token = auth.refresh_token
        self.client_id = auth.client_id
        self.source = source
        self.debug = debug
        self.logger = logger or logging.getLogger(__name__)
        self.on_token_refresh = on_token_refresh
        self._refreshing = False
        self._http = httpx.Client(timeout=timeout_s)

    def close(self) -> None:
        self._http.close()

    def is_authenticated(self) -> bool:
        return bool(self.access_token and self.client_id)

    def _log(self, message: str, *args: Any) -> None:
        if self.debug:
            self.logger.info("membase: " + message, *args)

    def _refresh_access_token(self) -> None:
        if self._refreshing:
            return
        if not self.refresh_token or not self.client_id:
            raise MembaseApiError(
                "Session expired. Run 'hermes membase login' to re-authenticate.",
                401,
            )

        self._refreshing = True
        try:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
            }
            response = self._http.post(
                f"{self.api_url}/oauth/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=data,
            )
            if response.status_code >= 400:
                raise MembaseApiError(
                    (
                        "Token refresh failed "
                        f"({response.status_code}). "
                        "Run 'hermes membase login' to re-authenticate."
                    ),
                    response.status_code,
                    response.text,
                )
            payload = response.json()
            self.access_token = str(payload.get("access_token") or "")
            maybe_refresh = payload.get("refresh_token")
            if isinstance(maybe_refresh, str) and maybe_refresh:
                self.refresh_token = maybe_refresh
            self.on_token_refresh and self.on_token_refresh(
                self.access_token,
                self.refresh_token,
            )
        finally:
            self._refreshing = False

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Any = None,
        json_body: dict[str, Any] | None = None,
        form_body: dict[str, Any] | None = None,
        expect_json: bool = True,
    ) -> Any:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        if form_body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif json_body is not None:
            headers["Content-Type"] = "application/json"

        url = f"{self.api_url}{path}"
        self._log("%s %s", method, path)
        response = self._http.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_body,
            data=form_body,
        )
        if response.status_code == 401 and self.refresh_token:
            self._refresh_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = self._http.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                data=form_body,
            )

        if response.status_code >= 400:
            raise MembaseApiError(
                f"Membase API error ({response.status_code}): {response.text}",
                response.status_code,
                response.text,
            )
        if not expect_json:
            return None
        try:
            return response.json()
        except json.JSONDecodeError as error:
            raise MembaseApiError(
                "Membase API returned non-JSON response",
                response.status_code,
                response.text[:200],
            ) from error

    def search(
        self,
        query: str,
        limit: int = 20,
        offset: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        timezone: str | None = None,
        sources: list[str] | None = None,
        project: str | None = None,
    ) -> list[dict[str, Any]]:
        params: list[tuple[str, str]] = [
            ("query", query),
            ("limit", str(limit)),
            ("format", "bundles"),
        ]
        if offset is not None:
            params.append(("offset", str(offset)))
        if date_from:
            params.append(("date_from", date_from))
        if date_to:
            params.append(("date_to", date_to))
        if timezone:
            params.append(("timezone", timezone))
        if project and project.strip():
            params.append(("project", project.strip()))
        if sources:
            params.extend(("sources", source) for source in sources if source)
        payload = self._request("GET", "/memory/search", params=params)
        bundles = payload.get("episodes") if isinstance(payload, dict) else None
        if not isinstance(bundles, list):
            return []
        episodes: list[dict[str, Any]] = []
        for item in bundles:
            if isinstance(item, dict) and "episode" in item:
                ep = item["episode"]
                if isinstance(ep, dict):
                    episodes.append(ep)
            elif isinstance(item, dict):
                episodes.append(item)
        return episodes

    def ingest(
        self,
        content: str,
        *,
        display_summary: str | None = None,
        project: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "content": content,
            "source": self.source,
            "channel": "api",
        }
        if display_summary:
            body["display_summary"] = display_summary
        if project and project.strip():
            body["project"] = project.strip()
        result = self._request("POST", "/memory/ingest", json_body=body)
        return result if isinstance(result, dict) else {"status": "unknown"}

    def get_profile(self) -> dict[str, Any]:
        payload = self._request("GET", "/user/settings")
        return payload if isinstance(payload, dict) else {}

    def delete_memory(self, episode_uuid: str) -> None:
        self._request(
            "DELETE",
            f"/memory/episodes/{episode_uuid}",
            expect_json=False,
        )

    def get_user_profile_memory(self) -> dict[str, Any] | None:
        try:
            payload = self._request("GET", "/memory/user_profile")
        except MembaseApiError as error:
            if error.status == 404:
                return None
            raise
        if isinstance(payload, dict) and payload.get("uuid"):
            return {"episode": payload, "edges": []}
        return None

    def register_connection(self) -> None:
        try:
            self._request(
                "POST",
                "/agents/connect",
                json_body={"source": self.source},
            )
        except MembaseApiError:
            # Fire-and-forget analytics signal. Not a hard failure.
            return

    def search_wiki(
        self,
        query: str,
        limit: int | None = None,
        collection_id: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"query": query}
        if limit is not None:
            params["limit"] = str(limit)
        if collection_id:
            params["collection_id"] = collection_id
        payload = self._request("GET", "/wiki/search", params=params)
        return payload if isinstance(payload, dict) else {"documents": []}

    def create_wiki_document(
        self,
        title: str,
        content: str,
        collection_id: str | None = None,
        summarize: bool = False,
    ) -> dict[str, Any]:
        payload = self._request(
            "POST",
            "/wiki/documents",
            json_body={
                "title": title,
                "content": content,
                "collection_id": collection_id,
                "source": self.source,
                "summarize": summarize,
            },
        )
        return payload if isinstance(payload, dict) else {}

    def update_wiki_document(
        self,
        doc_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._request(
            "PUT",
            f"/wiki/documents/{doc_id}",
            json_body=updates,
        )
        return payload if isinstance(payload, dict) else {}

    def delete_wiki_document(self, doc_id: str) -> None:
        self._request("DELETE", f"/wiki/documents/{doc_id}", expect_json=False)
