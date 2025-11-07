from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox, QSlider, QFileDialog, QMessageBox,
    QInputDialog
)
from PyQt6.QtCore import Qt
from src.core.vocabulary_processor import VocabularyProcessor

class VocabularyEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vocabulary Editor")
        self.setMinimumSize(700, 500)
        
        self.vocab_processor = VocabularyProcessor()
        self.current_profile = "default"
        self.current_terms = {}
        
        self.setup_ui()
        self.load_profile()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Profile:"))
        
        self.profile_combo = QComboBox()
        self.refresh_profiles()
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        profile_layout.addWidget(self.profile_combo)
        
        self.new_profile_button = QPushButton("New")
        self.new_profile_button.clicked.connect(self.create_profile)
        profile_layout.addWidget(self.new_profile_button)
        
        self.delete_profile_button = QPushButton("Delete")
        self.delete_profile_button.clicked.connect(self.delete_profile)
        profile_layout.addWidget(self.delete_profile_button)
        
        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self.import_profile)
        profile_layout.addWidget(self.import_button)
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_profile)
        profile_layout.addWidget(self.export_button)
        
        profile_layout.addStretch()
        layout.addLayout(profile_layout)
        
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Fuzzy Match Threshold:"))
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 5)
        self.threshold_slider.setValue(2)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(1)
        threshold_layout.addWidget(self.threshold_slider)
        
        self.threshold_label = QLabel("2")
        self.threshold_slider.valueChanged.connect(lambda v: self.threshold_label.setText(str(v)))
        threshold_layout.addWidget(self.threshold_label)
        
        layout.addLayout(threshold_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Match Term", "Replacement", "Actions"])
        
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(2, 100)
        layout.addWidget(self.table)
        
        add_layout = QHBoxLayout()
        self.match_input = QLineEdit()
        self.match_input.setPlaceholderText("Match term (phonetic)")
        add_layout.addWidget(self.match_input)
        
        self.replacement_input = QLineEdit()
        self.replacement_input.setPlaceholderText("Replacement (correct term)")
        add_layout.addWidget(self.replacement_input)
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_term)
        add_layout.addWidget(self.add_button)
        
        layout.addLayout(add_layout)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_profile)
        button_layout.addWidget(self.save_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def refresh_profiles(self):
        self.profile_combo.clear()
        profiles = self.vocab_processor.get_profile_names()
        
        if not profiles:
            self.vocab_processor.save_profile("default", {})
            profiles = ["default"]
            
        self.profile_combo.addItems(profiles)
        
        if self.current_profile in profiles:
            self.profile_combo.setCurrentText(self.current_profile)
        else:
            self.current_profile = profiles[0]
            
    def on_profile_changed(self, profile_name):
        if profile_name:
            self.current_profile = profile_name
            self.load_profile()
            
    def load_profile(self):
        profile = self.vocab_processor.get_profile(self.current_profile)
        if profile:
            self.current_terms = profile.terms.copy()
        else:
            self.current_terms = {}
            
        self.refresh_table()
        
    def refresh_table(self):
        self.table.setRowCount(len(self.current_terms))
        
        for row, (match, replacement) in enumerate(self.current_terms.items()):
            self.table.setItem(row, 0, QTableWidgetItem(match))
            self.table.setItem(row, 1, QTableWidgetItem(replacement))
            
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda checked, m=match: self.delete_term(m))
            self.table.setCellWidget(row, 2, delete_button)
            
    def add_term(self):
        match = self.match_input.text().strip()
        replacement = self.replacement_input.text().strip()
        
        if not match or not replacement:
            QMessageBox.warning(self, "Invalid Input", "Both match term and replacement are required.")
            return
            
        self.current_terms[match] = replacement
        self.match_input.clear()
        self.replacement_input.clear()
        self.refresh_table()
        
    def delete_term(self, match):
        if match in self.current_terms:
            del self.current_terms[match]
            self.refresh_table()
            
    def save_profile(self):
        if self.vocab_processor.save_profile(self.current_profile, self.current_terms):
            QMessageBox.information(self, "Success", f"Profile '{self.current_profile}' saved.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save profile.")
            
    def create_profile(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Enter profile name:")
        if ok and name:
            if self.vocab_processor.save_profile(name, {}):
                self.refresh_profiles()
                self.profile_combo.setCurrentText(name)
            else:
                QMessageBox.critical(self, "Error", "Failed to create profile.")
                
    def delete_profile(self):
        if self.current_profile == "default":
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete default profile.")
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete profile '{self.current_profile}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.vocab_processor.delete_profile(self.current_profile):
                self.refresh_profiles()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete profile.")
                
    def import_profile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Vocabulary",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            name, ok = QInputDialog.getText(self, "Profile Name", "Enter profile name:")
            if ok and name:
                if self.vocab_processor.import_profile(name, file_path):
                    self.refresh_profiles()
                    self.profile_combo.setCurrentText(name)
                    QMessageBox.information(self, "Success", f"Profile '{name}' imported.")
                else:
                    QMessageBox.critical(self, "Error", "Failed to import profile.")
                    
    def export_profile(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Vocabulary",
            f"{self.current_profile}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            if self.vocab_processor.export_profile(self.current_profile, file_path):
                QMessageBox.information(self, "Success", "Profile exported.")
            else:
                QMessageBox.critical(self, "Error", "Failed to export profile.")
                
    def get_threshold(self) -> int:
        return self.threshold_slider.value()
        
    def get_current_profile(self) -> str:
        return self.current_profile