from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QFileDialog, QLabel, QListWidget,
    QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
from src.core.transcriber import Transcriber
from src.core.queue_manager import QueueManager, QueueStatus
from src.ui.settings_dialog import SettingsDialog
from src.ui.model_dialog import ModelDialog
from src.ui.vocabulary_editor import VocabularyEditor
import json

class TranscribeWorker(QThread):
    finished = pyqtSignal(str, dict)
    error = pyqtSignal(str, str)
    progress = pyqtSignal(str, int, str)
    
    def __init__(self, item_id, audio_path, settings):
        super().__init__()
        self.item_id = item_id
        self.audio_path = audio_path
        self.settings = settings
        
    def run(self):
        try:
            self.progress.emit(self.item_id, 10, "Loading model...")
            transcriber = Transcriber(
                model_name=self.settings["model"], 
                device="cpu", 
                compute_type=self.settings["compute_type"]
            )
            
            self.progress.emit(self.item_id, 30, "Transcribing audio...")
            transcript = transcriber.transcribe(
                self.audio_path, 
                beam_size=self.settings["beam_size"], 
                batch_size=self.settings["batch_size"],
                enable_diarization=self.settings["enable_diarization"],
                hf_token=self.settings["hf_token"] if self.settings["hf_token"] else None,
                min_speakers=self.settings["min_speakers"],
                max_speakers=self.settings["max_speakers"],
                enable_vocabulary=self.settings.get("enable_vocabulary", False),
                vocabulary_profile=self.settings.get("vocabulary_profile", "default"),
                vocabulary_threshold=self.settings.get("vocabulary_threshold", 2)
            )
            
            self.progress.emit(self.item_id, 90, "Saving transcript...")
            output_path = f"{self.settings['output_dir']}/{Path(self.audio_path).stem}_transcript.json"
            transcriber.save_transcript(transcript, output_path)
            transcriber.unload_model()
            
            self.progress.emit(self.item_id, 100, "Complete")
            self.finished.emit(self.item_id, transcript)
        except Exception as e:
            self.error.emit(self.item_id, str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcription Tool")
        self.setMinimumSize(1200, 700)
        
        self.queue_manager = QueueManager()
        self.worker = None
        
        self.settings = {
            "preset": "Balanced",
            "model": "base",
            "beam_size": 5,
            "batch_size": 8,
            "compute_type": "int8",
            "output_dir": "outputs",
            "enable_diarization": False,
            "hf_token": "",
            "min_speakers": None,
            "max_speakers": None,
            "enable_vocabulary": False,
            "vocabulary_profile": "default",
            "vocabulary_threshold": 2
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        top_bar = QHBoxLayout()
        
        self.preset_label = QLabel(f"Preset: {self.settings['preset']}")
        self.model_label = QLabel(f"Model: {self.settings['model']}")
        
        self.vocabulary_button = QPushButton("Vocabulary")
        self.vocabulary_button.clicked.connect(self.open_vocabulary)
        
        self.models_button = QPushButton("Models")
        self.models_button.clicked.connect(self.open_models)
        
        self.settings_button = QPushButton("⚙")
        self.settings_button.setMaximumWidth(40)
        self.settings_button.clicked.connect(self.open_settings)
        
        self.add_files_button = QPushButton("+ Add Files")
        self.add_files_button.clicked.connect(self.add_files)
        self.clear_button = QPushButton("Clear Done")
        self.clear_button.clicked.connect(self.clear_completed)
        self.process_button = QPushButton("Start Processing")
        self.process_button.clicked.connect(self.start_processing)
        self.process_button.setEnabled(False)
        
        top_bar.addWidget(self.preset_label)
        top_bar.addWidget(self.model_label)
        top_bar.addWidget(self.vocabulary_button)
        top_bar.addWidget(self.models_button)
        top_bar.addWidget(self.settings_button)
        top_bar.addStretch()
        top_bar.addWidget(self.add_files_button)
        top_bar.addWidget(self.clear_button)
        top_bar.addWidget(self.process_button)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.queue_list = QListWidget()
        self.queue_list.setMinimumWidth(400)
        
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setPlaceholderText("Transcription preview will appear here...")
        
        splitter.addWidget(self.queue_list)
        splitter.addWidget(self.preview_area)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        
        layout.addLayout(top_bar)
        layout.addWidget(splitter)
        
    def open_vocabulary(self):
        dialog = VocabularyEditor(self)
        dialog.exec()
        
    def open_models(self):
        dialog = ModelDialog(self)
        dialog.exec()
        
    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.set_settings(self.settings)
        
        if dialog.exec():
            self.settings = dialog.get_settings()
            self.preset_label.setText(f"Preset: {self.settings['preset']}")
            self.model_label.setText(f"Model: {self.settings['model']}")
            
    def add_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Audio/Video Files",
            "",
            "Media Files (*.mp3 *.wav *.m4a *.mp4 *.mov *.avi *.mkv)"
        )
        
        for file_path in file_paths:
            item = self.queue_manager.add_item(
                file_path, 
                preset=self.settings["preset"],
                model=self.settings["model"]
            )
            self.add_queue_item_to_list(item)
            
        if self.queue_manager.items:
            self.process_button.setEnabled(True)
            
    def add_queue_item_to_list(self, item):
        list_item = QListWidgetItem(f"{item.filename} - {item.status.value} ({item.preset}/{item.model})")
        list_item.setData(Qt.ItemDataRole.UserRole, item.id)
        self.queue_list.addItem(list_item)
        
    def clear_completed(self):
        self.queue_manager.clear_completed()
        self.refresh_queue_list()
        
    def refresh_queue_list(self):
        self.queue_list.clear()
        for item in self.queue_manager.items:
            self.add_queue_item_to_list(item)
            
    def start_processing(self):
        if self.worker and self.worker.isRunning():
            return
            
        self.process_next_item()
        
    def process_next_item(self):
        next_item = self.queue_manager.get_next_queued()
        if not next_item:
            self.preview_area.append("\n✓ All items processed!")
            self.process_button.setEnabled(True)
            return
            
        self.queue_manager.update_status(next_item.id, QueueStatus.PROCESSING)
        self.refresh_queue_list()
        
        self.preview_area.append(f"\n=== Processing: {next_item.filename} ===")
        
        self.process_button.setEnabled(False)
        
        self.worker = TranscribeWorker(
            next_item.id,
            next_item.file_path,
            self.settings
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
    def on_progress(self, item_id, progress, message):
        self.queue_manager.update_status(item_id, QueueStatus.PROCESSING, progress)
        self.refresh_queue_list()
        self.preview_area.append(f"{message} ({progress}%)")
        
    def on_finished(self, item_id, transcript):
        self.queue_manager.update_status(item_id, QueueStatus.COMPLETE, 100)
        self.refresh_queue_list()
        
        vocab_status = " (vocab applied)" if transcript['metadata']['vocabulary_applied'] else ""
        self.preview_area.append(f"✓ Complete - {len(transcript['segments'])} segments{vocab_status}\n")
        
        for seg in transcript['segments'][:3]:
            self.preview_area.append(f"[{seg['start']:.1f}s] {seg['text']}")
            
        self.process_next_item()
        
    def on_error(self, item_id, error_msg):
        self.queue_manager.update_status(item_id, QueueStatus.ERROR, error=error_msg)
        self.refresh_queue_list()
        self.preview_area.append(f"✗ Error: {error_msg}\n")
        
        self.process_next_item()