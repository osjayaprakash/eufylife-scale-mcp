# Installing eufylife-scale-mcp

This guide takes you from nothing to asking Claude "how has my weight changed this month?".
It takes about 10 minutes.

## 1. Prerequisites

- **A Eufy smart scale** that syncs to the **EufyLife** app.
- **The EufyLife account's email and password.** If you sign in to EufyLife with Google
  or Apple, the account has no password yet: set one in the app (*Me* → *Account*) first.
- **[uv](https://docs.astral.sh/uv/)**, which installs Python 3.11+ and the dependencies
  for you:

  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # or, with Homebrew
  brew install uv
  ```

  ```powershell
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

- **An MCP client**, such as Claude Desktop or Claude Code.

## 2. Check the EufyLife account

1. Open the EufyLife app and confirm your recent weigh-ins appear. The server only sees
   measurements that have synced to the cloud.
2. Note the email, password, and the country the account was created in, as a two-letter
   code (`US`, `GB`, `DE`, …). If unsure, leave it as `US`.

Each person weighing in has a **member** profile in the app. The account owner is the
default member; family members can be named when you ask Claude.

## 3. Download and install

```bash
git clone https://github.com/osjayaprakash/eufylife-scale-mcp.git
cd eufylife-scale-mcp
uv sync
```

Note the full path of this folder; you'll need it below:

```bash
pwd
```

## 4. Check your credentials

Before connecting a client, confirm the server can log in and read data:

```bash
EUFYLIFE_EMAIL='you@example.com' \
EUFYLIFE_PASSWORD='your-password' \
EUFYLIFE_COUNTRY='US' \
uv run pytest -m live -q
```

`1 passed` means it works. If it fails, the error message tells you what to fix; see
[Troubleshooting](#troubleshooting).

On Windows (PowerShell), set the variables first:

```powershell
$env:EUFYLIFE_EMAIL = "you@example.com"
$env:EUFYLIFE_PASSWORD = "your-password"
$env:EUFYLIFE_COUNTRY = "US"
uv run pytest -m live -q
```

## 5. Connect your client

### Claude Desktop

1. Find the full path to `uv`. Claude Desktop doesn't always see your shell's `PATH`, so
   use the absolute path:

   ```bash
   which uv        # macOS / Linux, e.g. /Users/you/.local/bin/uv
   where uv        # Windows
   ```

2. Open the config file (*Settings* → *Developer* → *Edit Config*), or open it directly:

   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

3. Add the server under `mcpServers`, keeping any servers already there:

   ```json
   {
     "mcpServers": {
       "eufylife": {
         "command": "/Users/you/.local/bin/uv",
         "args": ["--directory", "/Users/you/eufylife-scale-mcp", "run", "eufylife-scale-mcp"],
         "env": {
           "EUFYLIFE_EMAIL": "you@example.com",
           "EUFYLIFE_PASSWORD": "your-password",
           "EUFYLIFE_COUNTRY": "US"
         }
       }
     }
   }
   ```

   On Windows, double every backslash in paths, for example
   `"C:\\Users\\you\\eufylife-scale-mcp"`.

4. Quit Claude Desktop completely and reopen it. The `eufylife` tools should appear in the
   tools menu.

### Claude Code

```bash
claude mcp add eufylife \
  -e EUFYLIFE_EMAIL=you@example.com \
  -e EUFYLIFE_PASSWORD=your-password \
  -e EUFYLIFE_COUNTRY=US \
  -- uv --directory /Users/you/eufylife-scale-mcp run eufylife-scale-mcp
```

This adds the server to the current project only. Add `--scope user` after `add` to make
it available in every project. Check it with `claude mcp list`.

### Other MCP clients

Run this command with the environment variables set; it speaks MCP over stdio:

```bash
uv --directory /path/to/eufylife-scale-mcp run eufylife-scale-mcp
```

## 6. Try it

Ask Claude:

- "What did I weigh this morning?"
- "How has my weight and body fat changed over the last 90 days?"
- "Compare my muscle mass now with a month ago."

If several people use the scale, name who you mean ("What's Ann's latest weight?"), or ask
Claude to list the members first.

## Optional: Langfuse tracing

To send a trace of each tool call to [Langfuse](https://langfuse.com):

1. Install the extra: `uv sync --extra langfuse`.
2. In the client config, change `run eufylife-scale-mcp` to
   `run --extra langfuse eufylife-scale-mcp`.
3. Add `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` to the server's `env`, plus
   `LANGFUSE_BASE_URL` if you don't use Langfuse Cloud.

By default, traces hold only tool names, timings, member IDs and error class names.
`LANGFUSE_CAPTURE_DATA=true` also sends measurements and member names; only turn it on
with a Langfuse instance you trust, such as a self-hosted one.

## Troubleshooting

| Message | What to do |
|---|---|
| `Missing required environment variable(s): …` | The client isn't passing the credentials. Check the `env` block (Claude Desktop) or `-e` flags (Claude Code). |
| `Invalid EUFYLIFE_COUNTRY …` | Use a two-letter country code such as `US` or `GB`. |
| `EufyLife rejected the login (code …). Check EUFYLIFE_EMAIL and EUFYLIFE_PASSWORD.` | Log in to the EufyLife app with the same email and password to confirm them. Passwords are used exactly as typed, including spaces. Google/Apple sign-in accounts need a password set in the app. |
| `No member matches …` | Ask Claude to list the members, then use one of those names or IDs. |
| `No scale measurements recorded for …` | That member has no synced weigh-ins. Open the EufyLife app to sync the scale. |
| `Rate limited by EufyLife…` | Wait for the time shown, then retry. |
| `EufyLife API error …` on every call | Eufy may have changed the app's API. Check for an update to this project. |
| `EufyLife returned unexpected data for …` | The API's response format changed. Open an issue with the tool name. |
| Tools don't appear in Claude Desktop | Use the absolute path to `uv`, check the JSON is valid, and fully quit and reopen Claude Desktop. Logs are in `~/Library/Logs/Claude/` (macOS) or `%APPDATA%\Claude\logs\` (Windows). |

## Updating

```bash
cd /path/to/eufylife-scale-mcp
git pull
uv sync
```

Then restart your MCP client.

## Uninstalling

1. Remove the `eufylife` entry from `claude_desktop_config.json`, or run
   `claude mcp remove eufylife`.
2. Delete the `eufylife-scale-mcp` folder.

## A note on your password

The client config stores the EufyLife password in plain text, readable by anyone who can
read that file. Use a password you don't use elsewhere.
