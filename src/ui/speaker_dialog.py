from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QFileDialog, QMessageBox, QInputDialog, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.core.speaker_manager import SpeakerManager

class ProfileWorker(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, speaker_manager, name, audio_path, hf_token):
        super().__init__()
        self.speaker_manager = speaker_manager
        self.name = name
        self.audio_path = audio_path
        self.hf_token = hf_token
        
    def run(self):
        try:
            success = self.speaker_manager.create_profile(self.name, self.audio_path, self.hf_token)
            if success:
                self.finished.emit(True, f"Profile '{self.name}' created successfully")
            else:
                self.finished.emit(False, "Failed to create profile")
        except Exception as e:
            self.finished.emit(False, str(e))

class SpeakerDialog(QDialog):
    def __init__(self, hf_token: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Speaker Profiles")
        self.setMinimumSize(700, 450)
        
        self.hf_token = hf_token
        self.speaker_manager = SpeakerManager()
        self.speaker_manager.load_profiles()
        self.worker = None
        
        self.setup_ui()
        self.refresh_profiles()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel(
            "Speaker profiles improve diarization accuracy.\n"
            "Upload 10-30 second reference audio clips of each speaker talking clearly."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Speaker Name", "Reference Audio", "Actions"])
        
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Speaker Profile")
        self.add_button.clicked.connect(self.add_profile)
        button_layout.addWidget(self.add_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def refresh_profiles(self):
        self.table.setRowCount(len(self.speaker_manager.profiles))
        
        for row, (name, profile) in enumerate(self.speaker_manager.profiles.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            
            from pathlib import Path
            ref_filename = Path(profile.reference_path).name
            self.table.setItem(row, 1, QTableWidgetItem(ref_filename))
            
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda checked, n=name: self.delete_profile(n))
            self.table.setCellWidget(row, 2, delete_button)
            
    def add_profile(self):
        if not self.hf_token:
            QMessageBox.warning(
                self,
                "Hugging Face Token Required",
                "Please set your Hugging Face token in Settings first.\n\n"
                "Get a token at: https://huggingface.co/settings/tokens"
            )
            return
            
        name, ok = QInputDialog.getText(
            self, 
            "Speaker Name", 
            "Enter speaker name (e.g., 'John Smith'):"
        )
        if not ok or not name:
            return
            
        name = name.strip()
        if name in self.speaker_manager.profiles:
            QMessageBox.warning(self, "Duplicate Name", f"Profile '{name}' already exists.")
            return
            
        audio_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Reference Audio (10-30 seconds of clear speech)",
            "",
            "Audio Files (*.wav *.mp3 *.m4a *.flac)"
        )
        
        if not audio_path:
            return
        
        progress = QProgressDialog("Creating speaker profile...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        self.worker = ProfileWorker(self.speaker_manager, name, audio_path, self.hf_token)
        self.worker.finished.connect(lambda success, msg: self.on_profile_created(success, msg, progress))
        self.worker.start()
            
    def on_profile_created(self, success, message, progress):
        progress.close()
        
        if success:
            self.refresh_profiles()
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", f"Failed to create profile:\n{message}")
            
    def delete_profile(self, name):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete speaker profile '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.speaker_manager.delete_profile(name):
                self.refresh_profiles()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete profile.")
                
    def get_speaker_manager(self) -> SpeakerManager:
        return self.speaker_manager