<h1 align="center">Membase Plugin for Hermes Agent</h1>

[![Hermes x Membase banner](<img width="1584" height="396" alt="Linkedin_aristo" src="https://github.com/user-attachments/assets/ed008859-174a-4469-845b-afa844511cfd" />
)](https://membase.so/?utm_source=github&utm_medium=hermes-membase)

<p align="center">
  Persistent long-term memory for Hermes Agent using hybrid vector search and a knowledge graph.
</p>

<p align="center">
  <a href="https://x.com/intent/follow?screen_name=mem_base"><img src="https://img.shields.io/badge/Follow%20on%20X-000000?style=for-the-badge&logo=x&logoColor=white" alt="Follow on X"></a>
  <a href="https://www.linkedin.com/company/aristotechnologies"><img src="https://img.shields.io/badge/Follow%20on%20LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="Follow on LinkedIn"></a>
  <a href="https://discord.gg/qfzXNdtmkv"><img src="https://img.shields.io/badge/Join%20Our%20Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Join Our Discord"></a>
  <a href="https://pypi.org/project/hermes-membase/"><img src="https://img.shields.io/pypi/v/hermes-membase?style=for-the-badge&color=blue" alt="PyPI version"></a>
</p>

<p align="center">
  <a href="https://membase.so/?utm_source=github&utm_medium=hermes-membase">Website</a> · <a href="https://docs.membase.so">Docs</a> · <a href="https://app.membase.so">Dashboard</a> · <a href="https://github.com/aristoapp/hermes-membase/issues">Issues</a>
</p>

---

Give your [Hermes Agent](https://hermes-agent.nousresearch.com/) persistent memory that survives across sessions. Membase uses hybrid vector search and a knowledge graph to remember not just text, but entities, relationships, and facts.

> **Free to start**: Sign up at [app.membase.so](https://app.membase.so) and connect in under a minute.

## Install

```bash
uv tool install hermes-membase && hermes-membase install
```

> Hermes installs `uv` automatically, so this works out of the box.  
> No `uv`? Use `pip install hermes-membase && hermes-membase install` instead.

This single command does everything:

1. Copies the self-contained plugin into `~/.hermes/plugins/membase/`
2. Sets `memory.provider: membase` in `~/.hermes/config.yaml`
3. Writes default config to `~/.hermes/membase.json`
4. Opens a browser window for OAuth login

Pass `--skip-login` to defer the login step and run `hermes-membase login` later.

## Setup

```bash
hermes-membase login
```

Opens a browser for OAuth authentication. Tokens are saved automatically, so there are no API keys to copy and paste.

## How It Works

Once installed, the plugin runs automatically on every Hermes session:

```txt
User message
    │
    ▼
┌─────────────────────────┐
│  Auto-Recall            │  Searches Membase for relevant memories
│  (queue_prefetch)       │  and injects them as context next turn
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  AI Response            │  Agent can call memory and wiki tools
│                         │  (membase_search, membase_wiki_add, etc.)
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  Auto-Capture           │  Buffers messages, flushes to Membase
│  (on_session_end)       │  for entity/relationship extraction
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  Mirror Built-in        │  Mirrors Hermes MEMORY.md writes to
│  (on_memory_write)      │  Membase for cross-session persistence
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  Membase Backend        │  Hybrid vector search + knowledge graph
│  (api.membase.so)       │
└─────────────────────────┘
```

- **Auto-Recall**: Before every AI turn, searches memory and wiki context (when enabled) and injects relevant snippets. Skips casual chat and short messages. Respects a `maxRecallChars` budget (default 4000) to avoid oversized context.
- **Auto-Capture**: Buffers conversation turns and flushes them to Membase at session end. Flushes after 5 minutes of silence or 20 messages. Requires at least 2 messages and 50+ characters total to avoid capturing one-off queries.
- **Mirror Built-in**: When Hermes writes to its built-in `MEMORY.md` via the `memory` tool, those writes are automatically mirrored to Membase in the background. A local hash index prevents duplicates.
- **Knowledge Graph**: Unlike simple vector-only memory, Membase uses hybrid vector search and a knowledge graph to store entities, relationships, and facts.

## AI Tools

The agent uses these tools autonomously during conversations:

| Tool | Description |
| --- | --- |
| `membase_search` | Search memories by semantic similarity. Supports date filtering (`date_from`, `date_to`, `timezone`) and source filtering (`sources`). Returns episode bundles with related facts. |
| `membase_store` | Save important information to long-term memory. Use for preferences, goals, decisions, and context. |
| `membase_forget` | Delete a memory. Shows matches first, then deletes after confirmation (two-step). |
| `membase_profile` | Retrieve user profile and related memories for session context. |
| `membase_wiki_search` | Search wiki documents for stable factual references. |
| `membase_wiki_add` | Create a wiki document from markdown content. |
| `membase_wiki_update` | Update title, content, or collection of an existing wiki document. |
| `membase_wiki_delete` | Delete a wiki document. |

## CLI Commands

```bash
hermes-membase install              # One-shot install and OAuth login
hermes-membase login                # OAuth login (PKCE): opens browser
hermes-membase logout               # Remove stored tokens
hermes-membase status               # Check API connectivity and profile
hermes-membase search "<query>"     # Search memories from the terminal
hermes-membase resync               # Rebuild mirror index from MEMORY.md
hermes-membase resync --dry-run     # Preview resync without writing
```

These are also available as `hermes membase <cmd>` from inside the Hermes TUI after installation.

## Configuration

Config is stored in `~/.hermes/membase.json`. All keys are optional and have sensible defaults:

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `tokenFile` | string | `~/.hermes/credentials/membase.json` | OAuth token cache path. Stored outside the plugin directory so it survives updates. |
| `autoRecall` | boolean | `false` | Inject relevant memories before every AI turn. |
| `autoWikiRecall` | boolean | `false` | Inject relevant wiki documents before every AI turn. |
| `autoCapture` | boolean | `true` | Automatically store conversations to Membase. |
| `mirrorBuiltin` | boolean | `true` | Mirror Hermes built-in memory writes to Membase. |
| `maxRecallChars` | number | `4000` | Max characters of injected memory context per turn (500-16000). |
| `debug` | boolean | `false` | Enable verbose debug logs. |

Example `~/.hermes/membase.json`:

```json
{
  "autoRecall": true,
  "autoCapture": true,
  "mirrorBuiltin": true,
  "maxRecallChars": 4000
}
```

## How Membase Differs

| | Simple vector memory | **Membase** |
| --- | --- | --- |
| **Storage** | Flat embeddings | Hybrid: vector embeddings + knowledge graph |
| **Search** | Vector similarity only | Vector + graph traversal (entities, relationships, facts) |
| **Extraction** | Store raw text | AI-powered entity/relationship extraction |
| **Auth** | API key | OAuth 2.0 with PKCE (no secrets to manage) |
| **Ingest** | Synchronous | Async pipeline (~100ms response, background graph sync) |

## Development

```bash
git clone https://github.com/aristoapp/hermes-membase.git
cd hermes-membase
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Contributing

Contributions welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## Links

- [Membase](https://membase.so/?utm_source=github&utm_medium=hermes-membase): Website
- [Dashboard](https://app.membase.so): Manage your memories
- [Docs](https://docs.membase.so): Full documentation
- [Hermes Agent](https://hermes-agent.nousresearch.com/): AI agent framework by Nous Research

## License

[MIT](./LICENSE)
