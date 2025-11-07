from pathlib import Path
from typing import Dict, List, Optional
import os

class ModelInfo:
    def __init__(self, name: str, size_mb: int, speed: str, accuracy: str):
        self.name = name
        self.size_mb = size_mb
        self.speed = speed
        self.accuracy = accuracy
        self.downloaded = False
        
MODEL_INFO = {
    "tiny": ModelInfo("tiny", 75, "~1min/hour", "Highest WER"),
    "base": ModelInfo("base", 140, "~2min/hour", "High WER"),
    "small": ModelInfo("small", 460, "~4min/hour", "Medium WER"),
    "medium": ModelInfo("medium", 1500, "~6-8min/hour", "~2% WER vs large"),
    "large-v2": ModelInfo("large-v2", 3000, "~15-20min/hour", "Best accuracy"),
    "large-v3": ModelInfo("large-v3", 3000, "~15-20min/hour", "Best accuracy"),
}

class ModelManager:
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            
    def get_available_models(self) -> List[ModelInfo]:
        models = list(MODEL_INFO.values())
        for model in models:
            model.downloaded = self.is_model_downloaded(model.name)
        return models
        
    def is_model_downloaded(self, model_name: str) -> bool:
        model_patterns = [
            f"models--Systran--faster-whisper-{model_name}",
            f"models--openai--whisper-{model_name}",
        ]
        
        for pattern in model_patterns:
            if any(self.cache_dir.glob(f"*{pattern}*")):
                return True
        return False
        
    def get_model_path(self, model_name: str) -> Optional[Path]:
        model_patterns = [
            f"models--Systran--faster-whisper-{model_name}",
            f"models--openai--whisper-{model_name}",
        ]
        
        for pattern in model_patterns:
            matches = list(self.cache_dir.glob(f"*{pattern}*"))
            if matches:
                return matches[0]
        return None
        
    def delete_model(self, model_name: str) -> bool:
        model_path = self.get_model_path(model_name)
        if not model_path or not model_path.exists():
            return False
            
        import shutil
        try:
            shutil.rmtree(model_path)
            return True
        except Exception as e:
            print(f"Error deleting model: {e}")
            return False
            
    def get_disk_usage(self) -> int:
        total_size = 0
        for model in MODEL_INFO.keys():
            model_path = self.get_model_path(model)
            if model_path and model_path.exists():
                for file in model_path.rglob("*"):
                    if file.is_file():
                        total_size += file.stat().st_size
        return total_size
        
    def get_model_size(self, model_name: str) -> int:
        model_path = self.get_model_path(model_name)
        if not model_path or not model_path.exists():
            return 0
            
        total_size = 0
        for file in model_path.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
        return total_size