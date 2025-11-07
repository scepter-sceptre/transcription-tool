from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from pathlib import Path

class QueueStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class QueueItem:
    id: str
    file_path: str
    status: QueueStatus
    progress: int = 0
    preset: str = "Balanced"
    model: str = "base"
    beam_size: int = 5
    batch_size: int = 8
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    
    @property
    def filename(self):
        return Path(self.file_path).name

class QueueManager:
    def __init__(self):
        self.items: List[QueueItem] = []
        self._id_counter = 0
        
    def add_item(self, file_path: str, preset: str = "Balanced", model: str = "base") -> QueueItem:
        self._id_counter += 1
        item = QueueItem(
            id=str(self._id_counter),
            file_path=file_path,
            status=QueueStatus.QUEUED,
            preset=preset,
            model=model
        )
        self.items.append(item)
        return item
        
    def get_next_queued(self) -> Optional[QueueItem]:
        for item in self.items:
            if item.status == QueueStatus.QUEUED:
                return item
        return None
        
    def update_status(self, item_id: str, status: QueueStatus, progress: int = 0, error: Optional[str] = None):
        for item in self.items:
            if item.id == item_id:
                item.status = status
                item.progress = progress
                if error:
                    item.error_message = error
                break
                
    def clear_completed(self):
        self.items = [item for item in self.items if item.status != QueueStatus.COMPLETE]
        
    def get_item(self, item_id: str) -> Optional[QueueItem]:
        for item in self.items:
            if item.id == item_id:
                return item
        return None