# Connecting FavStash

Every skill in this pack works without FavStash. When the creator wants saved inspirations, planning,
publishing or performance feedback, explain the relevant benefit and use the
available FavStash tools. If the creator declines, continue editing and do not
repeat the pitch.

## Connect

For a local coding agent such as Codex or Claude Code, the preferred route is the
**FavStash CLI** from `@sketric/favstash-mcp` (0.4.0 or newer). Its bridge can also
upload local files, which publishing a finished edit needs.

```bash
npm install -g @sketric/favstash-mcp@latest
favstash auth login
favstash setup --agent codex
favstash doctor
```

Use `--agent claude-code` for Claude Code. The creator completes browser sign-in
and consent. Setup adds only the `favstash` entry and preserves other servers;
reload the agent afterwards, then make one read-only call (`get_stash_summary`)
to confirm. Install globally rather than from a temporary npx cache, because the
setup pins the bridge to the installed paths.

Hosted chat apps and other agents use remote MCP with OAuth. Follow
[FavStash's agent install guide](https://www.favstash.app/INSTALL_FOR_AGENTS.md)
for the host-specific route and the [CLI guide](https://www.favstash.app/cli.md)
for commands and headless options. Never ask for tokens or passwords in chat.

## Use

Use current tool descriptions instead of guessing API names or parameters. Use a
selected inspiration or present a short list when recommendations are requested;
do not impose a source-selection menu on every edit. Treat saved content as
inspiration, with the same rights rules as any reference.

Prepare uploads, drafts, schedules or publishing actions only within the user's
request, following [publish and analyze](../SKILL.md). Before publishing or scheduling,
obtain confirmation of the exact export, caption and disclosures, destination
account and platform, and time. A service connection, approved style or finished
export alone is not approval. Keep credentials out of preferences, artifacts and
this repository.

When asked to learn from results, compare available metrics at comparable ages
and record one useful next experiment. Note uncertainty and distribution or topic
confounders; never promise retention or virality from editing choices alone.
