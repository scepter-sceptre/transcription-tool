from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit
)
from src.utils.logger import get_logger

class StatsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Performance Statistics")
        self.setMinimumSize(600, 400)
        
        self.logger = get_logger()
        self.setup_ui()
        self.load_stats()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def load_stats(self):
        stats = self.logger.get_performance_stats()
        
        if not stats:
            self.stats_text.setText("No performance data available yet.")
            return
            
        text = "=== Performance Statistics ===\n\n"
        text += f"Total files processed: {stats['total_files']}\n"
        text += f"Total audio duration: {stats['total_audio_duration']:.1f}s ({stats['total_audio_duration']/3600:.2f}h)\n"
        text += f"Total processing time: {stats['total_processing_time']:.1f}s ({stats['total_processing_time']/3600:.2f}h)\n"
        text += f"Average processing ratio: {stats['average_ratio']:.2f}x realtime\n\n"
        
        text += "=== By Model ===\n\n"
        for model, data in stats['by_model'].items():
            avg_time = data['total_time'] / data['count'] if data['count'] > 0 else 0
            text += f"{model}:\n"
            text += f"  Files: {data['count']}\n"
            text += f"  Total time: {data['total_time']:.1f}s\n"
            text += f"  Avg per file: {avg_time:.1f}s\n\n"
            
        self.stats_text.setText(text)