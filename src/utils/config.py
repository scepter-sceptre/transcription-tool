from pathlib import Path
import json
from typing import Dict, Any, List, Optional

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / "Library" / "Application Support" / "TranscriptionTool"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.recent_files_file = self.config_dir / "recent_files.json"
        
    def save_settings(self, settings: Dict[str, Any]):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def load_settings(self) -> Optional[Dict[str, Any]]:
        if not self.config_file.exists():
            return None
            
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return None
            
    def add_recent_file(self, file_path: str, transcript_path: str):
        recent = self.get_recent_files()
        
        entry = {
            "audio_path": file_path,
            "transcript_path": transcript_path,
            "filename": Path(file_path).name
        }
        
        recent = [r for r in recent if r["audio_path"] != file_path]
        recent.insert(0, entry)
        recent = recent[:10]
        
        try:
            with open(self.recent_files_file, 'w') as f:
                json.dump(recent, f, indent=2)
        except Exception as e:
            print(f"Error saving recent files: {e}")
            
    def get_recent_files(self) -> List[Dict[str, str]]:
        if not self.recent_files_file.exists():
            return []
            
        try:
            with open(self.recent_files_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading recent files: {e}")
            return []
            
    def clear_recent_files(self):
        if self.recent_files_file.exists():
            self.recent_files_file.unlink()