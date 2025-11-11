from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp
from pathlib import Path
import tempfile
from typing import cast

class DownloadWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)
    
    def __init__(self, url: str, output_dir: str):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            self.progress.emit(f"Downloading: {percent} | Speed: {speed} | ETA: {eta}")
        elif d['status'] == 'finished':
            self.progress.emit("Download complete, extracting audio...")
            
    def run(self):
        try:
            output_template = Path(self.output_dir) / "%(title)s.%(ext)s"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
                'outtmpl': str(output_template),
                'progress_hooks': [self.progress_hook],
                'quiet': False,
                'no_warnings': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(self.url, download=True)
                
                if info is None:
                    self.error.emit("Failed to extract video information")
                    return
                
                title = cast(dict, info).get('title', 'download')
                
                wav_files = sorted(
                    Path(self.output_dir).glob("*.wav"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )
                
                if not wav_files:
                    self.error.emit("No WAV file found after download")
                    return
                
                output_file = wav_files[0]
                
                if output_file.stat().st_size == 0:
                    self.error.emit("Downloaded file is empty. FFmpeg may not be installed.")
                    return
                
                self.finished.emit(str(output_file), title)
                
        except Exception as e:
            self.error.emit(str(e))

class DownloadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download from URL")
        self.setMinimumWidth(600)
        
        self.download_worker = None
        self.output_file = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel(
            "Download audio from YouTube, podcasts, or other sources.\n"
            "Requires ffmpeg: brew install ffmpeg"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://youtube.com/watch?v=...")
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(150)
        layout.addWidget(self.progress_text)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.progress_text.append("Error: Please enter a URL")
            return
            
        temp_dir = tempfile.gettempdir()
        
        self.progress_text.clear()
        self.progress_text.append(f"Starting download from: {url}")
        self.progress_bar.setVisible(True)
        self.download_button.setEnabled(False)
        self.url_input.setEnabled(False)
        
        self.download_worker = DownloadWorker(url, temp_dir)
        self.download_worker.progress.connect(self.on_progress)
        self.download_worker.finished.connect(self.on_finished)
        self.download_worker.error.connect(self.on_error)
        self.download_worker.start()
        
    def on_progress(self, message):
        self.progress_text.append(message)
        
    def on_finished(self, file_path, title):
        self.output_file = file_path
        self.progress_bar.setVisible(False)
        self.progress_text.append(f"\n✓ Download complete: {title}")
        self.progress_text.append(f"File saved to: {file_path}")
        self.accept()
        
    def on_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.progress_text.append(f"\n✗ Error: {error_msg}")
        self.download_button.setEnabled(True)
        self.url_input.setEnabled(True)
        
    def get_output_file(self):
        return self.output_file