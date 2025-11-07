from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.core.model_manager import ModelManager, MODEL_INFO
import whisperx

class DownloadWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str, str)
    
    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name
        
    def run(self):
        try:
            self.progress.emit(f"Downloading {self.model_name}...")
            whisperx.load_model(
                self.model_name,
                device="cpu",
                compute_type="int8",
                download_root=None
            )
            self.finished.emit(self.model_name)
        except Exception as e:
            self.error.emit(self.model_name, str(e))

class ModelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Management")
        self.setMinimumSize(700, 500)
        
        self.model_manager = ModelManager()
        self.download_worker = None
        
        self.setup_ui()
        self.refresh_models()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_layout = QHBoxLayout()
        self.disk_label = QLabel("Disk Usage: Calculating...")
        info_layout.addWidget(self.disk_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Model", "Size", "Speed", "Accuracy", "Status", "Action"
        ])
        
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_models)
        button_layout.addWidget(self.refresh_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def refresh_models(self):
        models = self.model_manager.get_available_models()
        
        disk_usage = self.model_manager.get_disk_usage()
        self.disk_label.setText(f"Disk Usage: {disk_usage / (1024**3):.2f} GB")
        
        self.table.setRowCount(len(models))
        
        for row, model in enumerate(models):
            self.table.setItem(row, 0, QTableWidgetItem(model.name))
            self.table.setItem(row, 1, QTableWidgetItem(f"{model.size_mb} MB"))
            self.table.setItem(row, 2, QTableWidgetItem(model.speed))
            self.table.setItem(row, 3, QTableWidgetItem(model.accuracy))
            
            status = "Downloaded" if model.downloaded else "Not Downloaded"
            self.table.setItem(row, 4, QTableWidgetItem(status))
            
            action_button = QPushButton("Delete" if model.downloaded else "Download")
            if model.downloaded:
                action_button.clicked.connect(lambda checked, m=model.name: self.delete_model(m))
            else:
                action_button.clicked.connect(lambda checked, m=model.name: self.download_model(m))
            
            self.table.setCellWidget(row, 5, action_button)
            
    def download_model(self, model_name):
        if self.download_worker and self.download_worker.isRunning():
            QMessageBox.warning(self, "Download in Progress", "A model is currently being downloaded.")
            return
            
        self.progress_bar.setVisible(True)
        self.status_label.setText(f"Downloading {model_name}...")
        self.refresh_button.setEnabled(False)
        
        self.download_worker = DownloadWorker(model_name)
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)
        self.download_worker.start()
        
    def delete_model(self, model_name):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete model '{model_name}'?\nThis will free up ~{MODEL_INFO[model_name].size_mb} MB.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.model_manager.delete_model(model_name):
                self.status_label.setText(f"✓ Deleted {model_name}")
                self.refresh_models()
            else:
                QMessageBox.warning(self, "Delete Failed", f"Could not delete {model_name}")
                
    def on_download_progress(self, message):
        self.status_label.setText(message)
        
    def on_download_finished(self, model_name):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✓ Downloaded {model_name}")
        self.refresh_button.setEnabled(True)
        self.refresh_models()
        
    def on_download_error(self, model_name, error):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✗ Download failed: {error}")
        self.refresh_button.setEnabled(True)
        QMessageBox.critical(self, "Download Error", f"Failed to download {model_name}:\n{error}")