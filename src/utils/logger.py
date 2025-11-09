import logging
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any, Optional

class TranscriptionLogger:
    def __init__(self):
        self.log_dir = Path.home() / "Library" / "Logs" / "TranscriptionTool"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.error_log = self.log_dir / "errors.log"
        self.performance_log = self.log_dir / "performance.json"
        self.session_log = self.log_dir / "sessions.json"
        
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.error_log),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('TranscriptionTool')
        
    def log_error(self, error_type: str, message: str, details: Optional[Dict] = None):
        self.logger.error(f"{error_type}: {message}")
        if details:
            self.logger.error(f"Details: {json.dumps(details)}")
            
    def log_performance(self, performance_data: Dict[str, Any]):
        performances = []
        if self.performance_log.exists():
            try:
                with open(self.performance_log, 'r') as f:
                    performances = json.load(f)
            except:
                performances = []
                
        performances.append({
            **performance_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        with open(self.performance_log, 'w') as f:
            json.dump(performances, f, indent=2)
            
    def log_session(self, session_data: Dict[str, Any]):
        sessions = []
        if self.session_log.exists():
            try:
                with open(self.session_log, 'r') as f:
                    sessions = json.load(f)
            except:
                sessions = []
                
        sessions.append({
            **session_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        with open(self.session_log, 'w') as f:
            json.dump(sessions, f, indent=2)
            
    def get_performance_stats(self) -> Dict[str, Any]:
        if not self.performance_log.exists():
            return {}
            
        try:
            with open(self.performance_log, 'r') as f:
                performances = json.load(f)
                
            if not performances:
                return {}
                
            total_files = len(performances)
            total_duration = sum(p.get("audio_duration", 0) for p in performances)
            total_processing = sum(p.get("processing_time", 0) for p in performances)
            
            avg_ratio = total_processing / total_duration if total_duration > 0 else 0
            
            by_model = {}
            for p in performances:
                model = p.get("model", "unknown")
                if model not in by_model:
                    by_model[model] = {"count": 0, "avg_ratio": 0, "total_time": 0}
                by_model[model]["count"] += 1
                by_model[model]["total_time"] += p.get("processing_time", 0)
                
            return {
                "total_files": total_files,
                "total_audio_duration": total_duration,
                "total_processing_time": total_processing,
                "average_ratio": avg_ratio,
                "by_model": by_model
            }
        except Exception as e:
            self.logger.error(f"Error getting performance stats: {e}")
            return {}

_logger_instance = None

def get_logger() -> TranscriptionLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TranscriptionLogger()
    return _logger_instance