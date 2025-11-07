from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QComboBox,
    QLineEdit, QLabel, QCheckBox, QSpinBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from typing import Dict, List, Optional
import json

class TranscriptEditor(QDialog):
    def __init__(self, transcript: Dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transcript Editor")
        self.setMinimumSize(1200, 700)
        
        self.transcript = transcript
        self.segments = transcript["segments"].copy()
        self.speakers = self.extract_speakers()
        self.modified = False
        
        self.setup_ui()
        self.load_segments()
        
    def extract_speakers(self) -> List[str]:
        speakers = set()
        for seg in self.segments:
            if seg.get("speaker"):
                speakers.add(seg["speaker"])
        return sorted(list(speakers))
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        top_bar = QHBoxLayout()
        
        metadata = self.transcript["metadata"]
        info_text = f"File: {metadata['source_file']} | Duration: {metadata['duration']:.1f}s | Model: {metadata['model']}"
        if metadata.get("vocabulary_applied"):
            info_text += " | Vocabulary: Applied"
        
        top_bar.addWidget(QLabel(info_text))
        top_bar.addStretch()
        
        layout.addLayout(top_bar)
        
        filter_bar = QHBoxLayout()
        
        filter_bar.addWidget(QLabel("Filter by confidence:"))
        self.confidence_check = QCheckBox("Show low confidence only")
        self.confidence_check.stateChanged.connect(self.apply_filters)
        filter_bar.addWidget(self.confidence_check)
        
        self.confidence_threshold = QSpinBox()
        self.confidence_threshold.setRange(0, 100)
        self.confidence_threshold.setValue(85)
        self.confidence_threshold.setSuffix("%")
        self.confidence_threshold.valueChanged.connect(self.apply_filters)
        filter_bar.addWidget(self.confidence_threshold)
        
        filter_bar.addWidget(QLabel("Speaker:"))
        self.speaker_filter = QComboBox()
        self.speaker_filter.addItem("All")
        self.speaker_filter.addItems(self.speakers)
        self.speaker_filter.currentTextChanged.connect(self.apply_filters)
        filter_bar.addWidget(self.speaker_filter)
        
        filter_bar.addStretch()
        layout.addLayout(filter_bar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Time", "Speaker", "Text", "Confidence", "Actions"
        ])
        
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        button_bar = QHBoxLayout()
        button_bar.addStretch()
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        self.save_button.setEnabled(False)
        button_bar.addWidget(self.save_button)
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_transcript)
        button_bar.addWidget(self.export_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_editor)
        button_bar.addWidget(self.close_button)
        
        layout.addLayout(button_bar)
        
    def load_segments(self):
        self.table.setRowCount(len(self.segments))
        
        for row, seg in enumerate(self.segments):
            time_text = f"{seg['start']:.1f}s - {seg['end']:.1f}s"
            time_item = QTableWidgetItem(time_text)
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, time_item)
            
            speaker_combo = QComboBox()
            if seg.get("speaker"):
                speaker_combo.addItems(self.speakers)
                speaker_combo.setCurrentText(seg["speaker"])
            else:
                speaker_combo.addItem("None")
            speaker_combo.currentTextChanged.connect(lambda text, r=row: self.on_speaker_changed(r, text))
            self.table.setCellWidget(row, 1, speaker_combo)
            
            text_item = QTableWidgetItem(seg["text"])
            self.table.setItem(row, 2, text_item)
            
            confidence = seg.get("confidence", 0.0) * 100
            confidence_item = QTableWidgetItem(f"{confidence:.1f}%")
            confidence_item.setFlags(confidence_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            if confidence < 70:
                confidence_item.setBackground(QColor(255, 200, 200))
            elif confidence < 85:
                confidence_item.setBackground(QColor(255, 255, 200))
            else:
                confidence_item.setBackground(QColor(200, 255, 200))
                
            self.table.setItem(row, 3, confidence_item)
            
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 0, 4, 0)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_segment(r))
            action_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 4, action_widget)
        
        self.table.itemChanged.connect(self.on_item_changed)
        
    def apply_filters(self):
        show_low_confidence = self.confidence_check.isChecked()
        threshold = self.confidence_threshold.value() / 100.0
        speaker = self.speaker_filter.currentText()
        
        for row in range(self.table.rowCount()):
            show_row = True
            
            if show_low_confidence:
                confidence = self.segments[row].get("confidence", 0.0)
                if confidence >= threshold:
                    show_row = False
                    
            if speaker != "All":
                seg_speaker = self.segments[row].get("speaker", "None")
                if seg_speaker != speaker:
                    show_row = False
                    
            self.table.setRowHidden(row, not show_row)
            
    def on_speaker_changed(self, row, speaker):
        self.segments[row]["speaker"] = speaker if speaker != "None" else None
        self.modified = True
        self.save_button.setEnabled(True)
        
    def on_item_changed(self, item):
        if item.column() == 2:
            row = item.row()
            self.segments[row]["text"] = item.text()
            self.modified = True
            self.save_button.setEnabled(True)
            
    def delete_segment(self, row):
        self.segments.pop(row)
        self.modified = True
        self.save_button.setEnabled(True)
        self.load_segments()
        
    def save_changes(self):
        self.transcript["segments"] = self.segments
        self.modified = False
        self.save_button.setEnabled(False)
        
    def export_transcript(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Transcript",
            f"{self.transcript['metadata']['source_file'].rsplit('.', 1)[0]}_edited.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.transcript, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Success", "Transcript exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")
                
    def close_editor(self):
        if self.modified:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        self.accept()
        
    def get_transcript(self) -> Dict:
        return self.transcript