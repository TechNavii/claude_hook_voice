#!/usr/bin/env python3
"""
Claude Hook Handler v3.0 - Japanese Voice Edition
================================================
Enhanced event handler with Japanese voice announcements for Claude Code.

New Features in v3.0:
- Japanese voice announcements using system TTS
- Configurable voice/sound modes
- Multilingual support framework
- Enhanced event descriptions in Japanese
"""

import sys
import json
import subprocess
import platform
import os
import re
import logging
import time
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum, auto
from functools import lru_cache
import hashlib


# Configuration Classes
@dataclass
class SoundConfig:
    """Configuration for sound playback"""
    volume: float = 1.0  # 0.0 to 1.0
    fallback_enabled: bool = True
    cache_sounds: bool = True
    max_duration: float = 5.0  # Maximum sound duration in seconds
    

@dataclass
class VoiceConfig:
    """Configuration for voice synthesis"""
    language: str = "ja_JP"  # Japanese by default
    voice_name: str = "Kyoko"  # Default Japanese voice
    rate: int = 200  # Words per minute
    volume: float = 1.0
    async_speak: bool = True  # Non-blocking speech
    

@dataclass 
class LogConfig:
    """Configuration for logging"""
    level: str = "INFO"
    file_path: Optional[Path] = None
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    rotate_size: int = 10 * 1024 * 1024  # 10MB
    

@dataclass
class HookConfig:
    """Main configuration container"""
    sounds_dir: Path
    sound_type: str = "beeps"
    mode: str = "voice"  # "sound", "voice", or "both"
    sound_config: SoundConfig = field(default_factory=SoundConfig)
    voice_config: VoiceConfig = field(default_factory=VoiceConfig)
    log_config: LogConfig = field(default_factory=LogConfig)
    debug_mode: bool = False
    test_mode: bool = False


# Enums for better type safety
class EventType(Enum):
    """Types of Claude events"""
    NOTIFICATION = "Notification"
    STOP = "Stop"
    SUBAGENT_STOP = "SubagentStop"
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    

class AudioBackend(Enum):
    """Available audio backends"""
    AFPLAY = auto()      # macOS
    SOX = auto()         # Cross-platform
    PAPLAY = auto()      # PulseAudio (Linux)
    APLAY = auto()       # ALSA (Linux)
    POWERSHELL = auto()  # Windows
    BEEP = auto()        # System beep fallback


# Japanese event descriptions
JAPANESE_EVENT_DESCRIPTIONS = {
    # System events
    "Notification": "クロードが準備完了しました",
    "Stop": "タスクが完了しました",
    "SubagentStop": "サブタスクが完了しました",
    "UserPromptSubmit": "ユーザーがプロンプトを送信しました",
    
    # Tools
    "Edit": "ファイルを編集しています",
    "MultiEdit": "複数の編集を実行しています",
    "Write": "ファイルを作成しています",
    "NotebookEdit": "ノートブックを編集しています",
    "TodoWrite": "タスクリストを更新しています",
    "Read": "ファイルを読み込んでいます",
    "Grep": "テキストを検索しています",
    "Task": "タスクを実行しています",
    "Bash": "コマンドを実行しています",
    "LS": "ディレクトリを一覧表示しています",
    "Glob": "ファイルパターンを検索しています",
    "exit_plan_mode": "計画モードを終了しています",
    "WebFetch": "ウェブページを取得しています",
    "WebSearch": "ウェブ検索を実行しています",
    
    # Bash commands
    "git_commit": "Gitコミットを作成しています",
    "git_push": "変更をプッシュしています",
    "git_pull": "変更をプルしています",
    "gh_pr": "プルリクエストを作成しています",
    "test": "テストを実行しています",
    "build": "ビルドを実行しています",
    "docker": "Dockerコマンドを実行しています",
    "npm": "NPMコマンドを実行しています",
    "python": "Pythonスクリプトを実行しています",
}


# Abstract base classes for extensibility
class SoundPlayer(ABC):
    """Abstract base class for sound players"""
    
    @abstractmethod
    def play(self, sound_path: Path, volume: float = 1.0) -> bool:
        """Play a sound file"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this player is available on the system"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this player"""
        pass


class VoicePlayer(ABC):
    """Abstract base class for voice synthesis"""
    
    @abstractmethod
    def speak(self, text: str, config: VoiceConfig) -> bool:
        """Speak the given text"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this voice synthesis is available"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this voice synthesis backend"""
        pass


# Concrete sound player implementations
class AfplaySoundPlayer(SoundPlayer):
    """macOS afplay sound player"""
    
    @property
    def name(self) -> str:
        return "afplay"
    
    def is_available(self) -> bool:
        try:
            subprocess.run(["which", "afplay"], capture_output=True, check=True)
            return True
        except:
            return False
    
    def play(self, sound_path: Path, volume: float = 1.0) -> bool:
        try:
            cmd = ["afplay", str(sound_path)]
            if volume < 1.0:
                cmd.extend(["-v", str(volume)])
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False


class SoxSoundPlayer(SoundPlayer):
    """Cross-platform sox sound player"""
    
    @property
    def name(self) -> str:
        return "sox"
    
    def is_available(self) -> bool:
        try:
            subprocess.run(["which", "play"], capture_output=True, check=True)
            return True
        except:
            return False
    
    def play(self, sound_path: Path, volume: float = 1.0) -> bool:
        try:
            cmd = ["play", str(sound_path), "vol", str(volume)]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False


class SystemBeepPlayer(SoundPlayer):
    """Fallback system beep player"""
    
    @property
    def name(self) -> str:
        return "system_beep"
    
    def is_available(self) -> bool:
        return True  # Always available as fallback
    
    def play(self, sound_path: Path, volume: float = 1.0) -> bool:
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.Popen(["osascript", "-e", "beep"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif system == "Linux":
                print("\a", end="", flush=True)  # ASCII bell
            elif system == "Windows":
                import winsound
                winsound.Beep(1000, 200)  # 1000Hz for 200ms
            else:
                print("\a", end="", flush=True)  # Fallback to ASCII bell
            return True
        except Exception:
            return False


# Concrete voice player implementations
class MacOSSayVoicePlayer(VoicePlayer):
    """macOS say command voice player"""
    
    @property
    def name(self) -> str:
        return "macos_say"
    
    def is_available(self) -> bool:
        try:
            subprocess.run(["which", "say"], capture_output=True, check=True)
            return platform.system() == "Darwin"
        except:
            return False
    
    def speak(self, text: str, config: VoiceConfig) -> bool:
        try:
            cmd = ["say", "-v", config.voice_name]
            
            # Add rate if different from default
            if config.rate != 200:
                cmd.extend(["-r", str(config.rate)])
            
            cmd.append(text)
            
            if config.async_speak:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
        except Exception as e:
            return False


class EspeakVoicePlayer(VoicePlayer):
    """Linux espeak voice player"""
    
    @property
    def name(self) -> str:
        return "espeak"
    
    def is_available(self) -> bool:
        try:
            subprocess.run(["which", "espeak"], capture_output=True, check=True)
            return True
        except:
            return False
    
    def speak(self, text: str, config: VoiceConfig) -> bool:
        try:
            # espeak doesn't support Japanese well, but we'll try
            cmd = ["espeak", "-s", str(config.rate)]
            
            # Try to use Japanese voice if available
            if config.language.startswith("ja"):
                cmd.extend(["-v", "ja"])
            
            cmd.append(text)
            
            if config.async_speak:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True
        except Exception:
            return False


# Pattern matching system
@dataclass
class Pattern:
    """A pattern for matching events or commands"""
    regex: str
    sound: str
    voice_key: str  # Key for Japanese description
    priority: int = 0
    description: str = ""
    
    def matches(self, text: str) -> bool:
        """Check if this pattern matches the given text"""
        return bool(re.match(self.regex, text, re.IGNORECASE))


class EventMatcher:
    """Sophisticated event matching system"""
    
    def __init__(self):
        self.patterns: Dict[str, List[Pattern]] = {
            "system_events": [
                Pattern("Notification", "ready", "Notification", 100, "Claude is ready"),
                Pattern("Stop", "complete", "Stop", 100, "Task completed"),
                Pattern("SubagentStop", "complete", "SubagentStop", 100, "Subtask completed"),
                Pattern("UserPromptSubmit", "prompt", "UserPromptSubmit", 100, "User prompt"),
            ],
            "tools": [
                Pattern("Edit", "edit", "Edit", 90, "File editing"),
                Pattern("MultiEdit", "edit", "MultiEdit", 90, "Multiple edits"),
                Pattern("Write", "write", "Write", 90, "File creation"),
                Pattern("NotebookEdit", "edit", "NotebookEdit", 90, "Notebook editing"),
                Pattern("TodoWrite", "list", "TodoWrite", 80, "Todo list update"),
                Pattern("Read", "read", "Read", 70, "File reading"),
                Pattern("Grep", "search", "Grep", 70, "Text search"),
                Pattern("Task", "task", "Task", 70, "Task execution"),
                Pattern("LS", "list", "LS", 70, "Directory listing"),
                Pattern("Glob", "search", "Glob", 70, "File pattern search"),
                Pattern("exit_plan_mode", "complete", "exit_plan_mode", 70, "Exit plan mode"),
                Pattern("WebFetch", "web", "WebFetch", 70, "Web fetch"),
                Pattern("WebSearch", "search", "WebSearch", 70, "Web search"),
            ],
            "bash_commands": [
                Pattern(r'^git\s+commit', "commit", "git_commit", 95, "Git commit"),
                Pattern(r'^git\s+push', "push", "git_push", 95, "Git push"),
                Pattern(r'^git\s+pull', "pull", "git_pull", 95, "Git pull"),
                Pattern(r'^gh\s+pr', "pr", "gh_pr", 95, "GitHub PR"),
                Pattern(r'^npm\s+test|^yarn\s+test', "test", "test", 90, "JavaScript tests"),
                Pattern(r'^pytest|^python.*test', "test", "test", 90, "Python tests"),
                Pattern(r'^go\s+test', "test", "test", 90, "Go tests"),
                Pattern(r'^cargo\s+test', "test", "test", 90, "Rust tests"),
                Pattern(r'^make', "build", "build", 85, "Make build"),
                Pattern(r'^docker', "docker", "docker", 85, "Docker command"),
                Pattern(r'^npm', "npm", "npm", 85, "NPM command"),
                Pattern(r'^python', "python", "python", 85, "Python command"),
                Pattern(r'.*', "bash", "Bash", 0, "Generic bash command"),
            ]
        }
    
    def find_match(self, event_data: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """Find the best matching sound and voice key for an event"""
        event_name = event_data.get("hook_event_name", "")
        tool_name = event_data.get("tool_name", "")
        
        # Check system events first
        for pattern in self.patterns["system_events"]:
            if pattern.matches(event_name):
                return pattern.sound, pattern.voice_key
        
        # Check tool patterns
        for pattern in self.patterns["tools"]:
            if pattern.matches(tool_name):
                return pattern.sound, pattern.voice_key
        
        # Special handling for bash commands
        if tool_name == "Bash" and event_name == "PreToolUse":
            command = event_data.get("tool_input", {}).get("command", "")
            
            # Find all matching patterns and use the highest priority one
            matches = []
            for pattern in self.patterns["bash_commands"]:
                if pattern.matches(command):
                    matches.append(pattern)
            
            if matches:
                best_match = max(matches, key=lambda p: p.priority)
                return best_match.sound, best_match.voice_key
        
        return None, None


# Main audio manager
class AudioManager:
    """Manages audio playback with multiple backends and fallbacks"""
    
    def __init__(self, config: HookConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.sound_players = self._init_sound_players()
        self.voice_players = self._init_voice_players()
        self._sound_cache: Dict[str, Path] = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging configuration"""
        logger = logging.getLogger("ClaudeHook")
        logger.setLevel(getattr(logging, self.config.log_config.level))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(logging.Formatter(self.config.log_config.format))
        logger.addHandler(console_handler)
        
        # File handler if specified
        if self.config.log_config.file_path:
            file_handler = logging.FileHandler(self.config.log_config.file_path)
            file_handler.setFormatter(logging.Formatter(self.config.log_config.format))
            logger.addHandler(file_handler)
        
        return logger
    
    def _init_sound_players(self) -> List[SoundPlayer]:
        """Initialize available sound players in order of preference"""
        player_classes = [
            AfplaySoundPlayer,
            SoxSoundPlayer,
            SystemBeepPlayer,
        ]
        
        players = []
        for player_class in player_classes:
            player = player_class()
            if player.is_available():
                players.append(player)
                self.logger.debug(f"Initialized {player.name} sound player")
        
        if not players:
            self.logger.warning("No audio players available, using system beep")
            players.append(SystemBeepPlayer())
        
        return players
    
    def _init_voice_players(self) -> List[VoicePlayer]:
        """Initialize available voice players"""
        player_classes = [
            MacOSSayVoicePlayer,
            EspeakVoicePlayer,
        ]
        
        players = []
        for player_class in player_classes:
            player = player_class()
            if player.is_available():
                players.append(player)
                self.logger.debug(f"Initialized {player.name} voice player")
        
        return players
    
    @lru_cache(maxsize=32)
    def _find_sound_file(self, sound_name: str) -> Optional[Path]:
        """Find a sound file with caching"""
        sounds_dir = self.config.sounds_dir / self.config.sound_type
        
        # Check various audio formats
        for ext in ['.wav', '.mp3', '.ogg', '.m4a', '.flac']:
            sound_path = sounds_dir / f"{sound_name}{ext}"
            if sound_path.exists():
                return sound_path
        
        return None
    
    def play_sound(self, sound_name: str) -> bool:
        """Play a sound with fallback mechanisms"""
        # Security check
        if "/" in sound_name or "\\" in sound_name or ".." in sound_name:
            self.logger.error(f"Invalid sound name: {sound_name}")
            return False
        
        # Find sound file
        sound_path = self._find_sound_file(sound_name)
        
        if not sound_path:
            self.logger.warning(f"Sound file not found: {sound_name}")
            if self.config.sound_config.fallback_enabled:
                self.logger.info("Using system beep as fallback")
                return self._play_system_beep()
            return False
        
        # Try each player until one succeeds
        for player in self.sound_players:
            if player.play(sound_path, self.config.sound_config.volume):
                self.logger.debug(f"Played {sound_name} using {player.name}")
                return True
        
        # All players failed, try system beep
        if self.config.sound_config.fallback_enabled:
            return self._play_system_beep()
        
        return False
    
    def speak_text(self, text: str) -> bool:
        """Speak text using available voice synthesis"""
        if not self.voice_players:
            self.logger.warning("No voice players available")
            return False
        
        # Try each voice player until one succeeds
        for player in self.voice_players:
            if player.speak(text, self.config.voice_config):
                self.logger.debug(f"Spoke text using {player.name}")
                return True
        
        self.logger.error("All voice players failed")
        return False
    
    def _play_system_beep(self) -> bool:
        """Play a system beep as ultimate fallback"""
        beep_player = SystemBeepPlayer()
        return beep_player.play(Path("/dev/null"))  # Path is ignored for beep


# Main hook handler
class HookHandler:
    """Main handler for Claude Code hooks"""
    
    def __init__(self, config: HookConfig):
        self.config = config
        self.audio_manager = AudioManager(config)
        self.event_matcher = EventMatcher()
        self.logger = logging.getLogger("ClaudeHook.Handler")
        
    def handle_event(self, event_data: Dict[str, Any]) -> None:
        """Process a hook event from Claude"""
        # Log the event
        self._log_event(event_data)
        
        # Find matching sound and voice description
        sound_name, voice_key = self.event_matcher.find_match(event_data)
        
        if not sound_name and not voice_key:
            self.logger.debug("No matching sound or voice for event")
            return
        
        # Handle based on mode
        if self.config.mode == "sound" and sound_name:
            self.logger.info(f"Playing sound '{sound_name}' for event")
            if not self.config.test_mode:
                self.audio_manager.play_sound(sound_name)
                
        elif self.config.mode == "voice" and voice_key:
            japanese_text = JAPANESE_EVENT_DESCRIPTIONS.get(voice_key, voice_key)
            self.logger.info(f"Speaking: {japanese_text}")
            if not self.config.test_mode:
                self.audio_manager.speak_text(japanese_text)
                
        elif self.config.mode == "both":
            if voice_key:
                japanese_text = JAPANESE_EVENT_DESCRIPTIONS.get(voice_key, voice_key)
                self.logger.info(f"Speaking: {japanese_text}")
                if not self.config.test_mode:
                    self.audio_manager.speak_text(japanese_text)
            if sound_name:
                self.logger.info(f"Playing sound '{sound_name}' for event")
                if not self.config.test_mode:
                    time.sleep(0.1)  # Small delay between voice and sound
                    self.audio_manager.play_sound(sound_name)
        
        if self.config.test_mode:
            self.logger.info(f"TEST MODE: Would play {sound_name} and/or speak {voice_key}")
    
    def _log_event(self, event_data: Dict[str, Any]) -> None:
        """Log event data for debugging/auditing"""
        log_path = Path(__file__).parent / "hook_handler_v3.jsonl"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to log event: {e}")


# Configuration loader
def load_config() -> HookConfig:
    """Load configuration from environment or defaults"""
    script_dir = Path(__file__).parent
    
    # Check for config file
    config_file = script_dir / "hook_config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                config_data = json.load(f)
                # Parse config data here
        except Exception:
            pass
    
    # Default configuration
    mode = os.environ.get("CLAUDE_HOOK_MODE", "voice")
    voice_name = os.environ.get("CLAUDE_HOOK_VOICE", "Kyoko")
    
    return HookConfig(
        sounds_dir=script_dir / "sounds",
        sound_type=os.environ.get("CLAUDE_HOOK_SOUND_TYPE", "beeps"),
        mode=mode,
        voice_config=VoiceConfig(voice_name=voice_name),
        debug_mode=os.environ.get("CLAUDE_HOOK_DEBUG", "").lower() == "true",
        test_mode=os.environ.get("CLAUDE_HOOK_TEST", "").lower() == "true",
    )


# Main entry point
def main():
    """Main program entry point"""
    try:
        # Load configuration
        config = load_config()
        
        # Create handler
        handler = HookHandler(config)
        
        # Read event data from stdin
        event_data = json.load(sys.stdin)
        
        # Handle the event
        handler.handle_event(event_data)
        
        # Always exit successfully to not interrupt Claude
        sys.exit(0)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        # Still exit with 0 to not interrupt Claude
        sys.exit(0)


if __name__ == "__main__":
    main()