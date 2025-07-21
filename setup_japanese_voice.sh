#!/bin/bash

# Setup script for Claude Code Japanese Voice Hooks

echo "🎌 Claude Code Japanese Voice Setup"
echo "==================================="
echo

# Check if settings.json exists
if [ ! -f ~/.claude/settings.json ]; then
    echo "❌ Error: ~/.claude/settings.json not found"
    echo "Please run Claude Code at least once to create the settings file"
    exit 1
fi

# Function to add to shell profile
add_to_profile() {
    local profile_file=$1
    local export_line='export CLAUDE_HOOK_MODE="voice"'
    
    if grep -q "CLAUDE_HOOK_MODE" "$profile_file" 2>/dev/null; then
        echo "✓ CLAUDE_HOOK_MODE already in $profile_file"
    else
        echo "" >> "$profile_file"
        echo "# Claude Code Japanese Voice" >> "$profile_file"
        echo "$export_line" >> "$profile_file"
        echo 'export CLAUDE_HOOK_VOICE="Kyoko"' >> "$profile_file"
        echo "✓ Added to $profile_file"
    fi
}

# Detect shell and update profile
if [ -n "$ZSH_VERSION" ]; then
    echo "Detected Zsh shell"
    add_to_profile ~/.zshrc
elif [ -n "$BASH_VERSION" ]; then
    echo "Detected Bash shell"
    add_to_profile ~/.bashrc
fi

# Set for current session
export CLAUDE_HOOK_MODE="voice"
export CLAUDE_HOOK_VOICE="Kyoko"

echo
echo "✅ Setup complete!"
echo
echo "Current settings:"
echo "  CLAUDE_HOOK_MODE=$CLAUDE_HOOK_MODE"
echo "  CLAUDE_HOOK_VOICE=$CLAUDE_HOOK_VOICE"
echo
echo "Available modes:"
echo "  voice - Japanese voice announcements only"
echo "  sound - Sound effects only"
echo "  both  - Both voice and sounds"
echo
echo "Available Japanese voices:"
echo "  Kyoko (default), Eddy, Flo, Grandma, Grandpa"
echo "  Reed, Rocko, Sandy, Shelley"
echo
echo "To change settings:"
echo "  export CLAUDE_HOOK_MODE='both'"
echo "  export CLAUDE_HOOK_VOICE='Sandy'"
echo
echo "The settings have been saved to your shell profile."
echo "Please restart your terminal or run: source ~/.zshrc (or ~/.bashrc)"
echo
echo "🎉 Enjoy Japanese voice announcements in Claude Code!"