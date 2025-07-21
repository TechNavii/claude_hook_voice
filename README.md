# Claude Code Hooks with Japanese Voice

## Overview

This guide covers the complete setup of Claude Code hooks with Japanese voice announcements and smart event matching.

## What's Configured

### 1. **All Hook Events**
Your `~/.claude/settings.json` now handles:
- **PreToolUse**: Before any tool runs (with smart matching)
- **PostToolUse**: After successful tool completion
- **Notification**: When Claude is ready or needs permission
- **Stop**: When main agent finishes
- **SubagentStop**: When subagents complete
- **PreCompact**: Before context compaction
- **UserPromptSubmit**: When you submit a prompt

### 2. **Smart Tool Matching**
Tools are grouped logically:
- **File Operations**: Edit, Write, MultiEdit, NotebookEdit
- **Reading/Searching**: Read, Grep, Glob, LS
- **Task Management**: TodoWrite, Task, exit_plan_mode
- **Web Operations**: WebFetch, WebSearch
- **Bash Commands**: With intelligent command recognition
- **GitHub Operations**: All MCP GitHub tools

### 3. **Japanese Voice Announcements**

#### Common Announcements You'll Hear:
- 📝 "ファイルを編集しています" - When editing files
- 🔍 "テキストを検索しています" - When searching
- 💾 "Gitコミットを作成しています" - When committing
- ✅ "タスクが完了しました" - When tasks complete
- 🌐 "ウェブ検索を実行しています" - For web searches
- 🧪 "テストを実行しています" - When running tests

## Quick Start

### Enable Japanese Voice (One Time)
```bash
# Run the setup script
./setup_japanese_voice.sh

# Or manually:
export CLAUDE_HOOK_MODE="voice"
export CLAUDE_HOOK_VOICE="Kyoko"
```

### Test It Works
```bash
# This should trigger a Japanese announcement
echo '{"hook_event_name": "Notification"}' | python3 /Users/tooru/Desktop/coding_test/claude_hook_v3.py
```

## Configuration Options

### Voice Modes
```bash
# Japanese voice only (recommended)
export CLAUDE_HOOK_MODE="voice"

# Sound effects only
export CLAUDE_HOOK_MODE="sound"

# Both voice and sounds
export CLAUDE_HOOK_MODE="both"
```

### Voice Selection
```bash
# Default female voice
export CLAUDE_HOOK_VOICE="Kyoko"

# Alternative voices
export CLAUDE_HOOK_VOICE="Sandy"    # Different female voice
export CLAUDE_HOOK_VOICE="Grandma"  # Elderly female
export CLAUDE_HOOK_VOICE="Grandpa"  # Elderly male
export CLAUDE_HOOK_VOICE="Reed"     # Male voice
```

### Debug Mode
```bash
# Enable detailed logging
export CLAUDE_HOOK_DEBUG="true"

# Test mode (no actual sounds)
export CLAUDE_HOOK_TEST="true"
```

## Smart Event Matching Examples

### Git Operations
When you run git commands, you'll hear specific announcements:
- `git commit` → "Gitコミットを作成しています"
- `git push` → "変更をプッシュしています"
- `git pull` → "変更をプルしています"
- `gh pr create` → "プルリクエストを作成しています"

### Test Execution
Different test frameworks are recognized:
- `pytest` → "テストを実行しています"
- `npm test` → "テストを実行しています"
- `go test` → "テストを実行しています"
- `cargo test` → "テストを実行しています"

### File Operations
- Editing → "ファイルを編集しています"
- Creating → "ファイルを作成しています"
- Reading → "ファイルを読み込んでいます"

## Troubleshooting

### No Sound?
1. Check volume: System Preferences > Sound
2. Test directly: `say -v Kyoko "テスト"`
3. Check env vars: `echo $CLAUDE_HOOK_MODE`

### Wrong Voice?
List available: `say -v "?" | grep ja_JP`

### Not Working?
1. Check permissions: `ls -la ~/.claude/settings.json`
2. Validate JSON: `python3 -m json.tool ~/.claude/settings.json`
3. Check logs: Look for errors in Claude Code output

## Advanced Customization

### Add Custom Announcements
Edit `/Users/tooru/Desktop/coding_test/claude_hook_v3.py`:
```python
JAPANESE_EVENT_DESCRIPTIONS = {
    "YourEvent": "あなたのカスタムメッセージ",
    # Add more...
}
```

### Create Tool-Specific Hooks
In `~/.claude/settings.json`:
```json
{
  "PreToolUse": [
    {
      "matcher": "YourTool",
      "hooks": [
        {
          "type": "command",
          "command": "your-custom-command"
        }
      ]
    }
  ]
}
```

## Security Notes

1. **Hooks run with your permissions** - Be careful with commands
2. **Validate all inputs** - The hook script sanitizes file paths
3. **Test before deploying** - Use TEST mode first
4. **Review logs regularly** - Check `hook_handler_v3.jsonl`

## Maintenance

### Update Hook Script
```bash
# Pull latest version
cd /Users/tooru/Desktop/coding_test
# Edit claude_hook_v3.py as needed
```

### View Logs
```bash
# See recent events
tail -f /Users/tooru/Desktop/coding_test/hook_handler_v3.jsonl
```

### Disable Temporarily
```bash
# Turn off voice
export CLAUDE_HOOK_MODE="sound"

# Or completely disable in settings.json
```

## Next Steps

1. **Restart Claude Code** to load new settings
2. **Test with simple command** like creating a file
3. **Adjust voice/volume** to your preference
4. **Enjoy the feedback!** 🎌

---

Happy coding with Japanese voice 
