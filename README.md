# Mac Computer Use

Native macOS computer control for Claude via Anthropic's Computer Use API or MCP (Model Context Protocol).

> [!CAUTION]
> Claude can control your entire Mac. Be careful what you authorize.

## Quick Start

### Prerequisites

```bash
brew install cliclick
```

Required: macOS 15.7+, Python 3.12+

### Installation

```bash
git clone https://github.com/tomascupr/mac_computer_use.git
cd mac_computer_use
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Option 1: MCP Server (Recommended)

Use with Claude Desktop, Claude Code, or any MCP client:

```bash
python mcp_server.py
```

**Claude Desktop Configuration** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mac-computer-control": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/mac_computer_use/mcp_server.py"]
    }
  }
}
```

**Available Tools:**
- `screenshot` - Capture screen as image
- `click` / `click_at` - Mouse clicks
- `type_text` - Type text
- `press_key` - Keyboard (supports combos like `cmd+c`)
- `mouse_move` - Move cursor
- `right_click` / `double_click` - Mouse actions

### Option 2: Streamlit UI

Interactive web interface:

```bash
# Create .env file
echo "API_PROVIDER=anthropic" >> .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env

streamlit run streamlit.py
```

Open http://localhost:8501

## Features

- Native macOS screen capture and control
- No Docker required
- Works with Claude Desktop, Claude Code, Cursor, and other MCP clients
- Automatic resolution scaling for optimal performance
- Keyboard shortcuts and mouse control via cliclick

## Notes

- Recommended resolution: 1366x768 (auto-scaled from higher resolutions)
- API subject to change - see [Anthropic release notes](https://docs.anthropic.com/en/release-notes/api)
