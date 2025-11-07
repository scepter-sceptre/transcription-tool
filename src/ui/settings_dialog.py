from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSpinBox, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from src.core.vocabulary_processor import VocabularyProcessor

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        self.vocab_processor = VocabularyProcessor()
        
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
        layout = QVBoxLayout(self)
        
        preset_group = QGroupBox("Processing Preset")
        preset_layout = QFormLayout()
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Fast", "Balanced", "Accurate"])
        self.preset_combo.setCurrentText(self.settings["preset"])
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_layout.addRow("Preset:", self.preset_combo)
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        model_group = QGroupBox("Model Configuration")
        model_layout = QFormLayout()
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large-v2", "large-v3"])
        self.model_combo.setCurrentText(self.settings["model"])
        model_layout.addRow("Model:", self.model_combo)
        
        self.beam_spin = QSpinBox()
        self.beam_spin.setRange(1, 10)
        self.beam_spin.setValue(self.settings["beam_size"])
        model_layout.addRow("Beam Size:", self.beam_spin)
        
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 32)
        self.batch_spin.setValue(self.settings["batch_size"])
        model_layout.addRow("Batch Size:", self.batch_spin)
        
        self.compute_combo = QComboBox()
        self.compute_combo.addItems(["int8", "float16", "float32"])
        self.compute_combo.setCurrentText(self.settings["compute_type"])
        model_layout.addRow("Compute Type:", self.compute_combo)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        vocab_group = QGroupBox("Vocabulary")
        vocab_layout = QFormLayout()
        
        self.vocab_check = QCheckBox()
        self.vocab_check.setChecked(self.settings["enable_vocabulary"])
        vocab_layout.addRow("Enable Vocabulary:", self.vocab_check)
        
        self.vocab_profile_combo = QComboBox()
        self.refresh_vocab_profiles()
        vocab_layout.addRow("Profile:", self.vocab_profile_combo)
        
        self.vocab_threshold_spin = QSpinBox()
        self.vocab_threshold_spin.setRange(0, 5)
        self.vocab_threshold_spin.setValue(self.settings["vocabulary_threshold"])
        vocab_layout.addRow("Fuzzy Threshold:", self.vocab_threshold_spin)
        
        vocab_group.setLayout(vocab_layout)
        layout.addWidget(vocab_group)
        
        diarization_group = QGroupBox("Diarization")
        diarization_layout = QFormLayout()
        
        self.diarization_check = QCheckBox()
        self.diarization_check.setChecked(self.settings["enable_diarization"])
        diarization_layout.addRow("Enable Diarization:", self.diarization_check)
        
        self.hf_token_edit = QLineEdit()
        self.hf_token_edit.setPlaceholderText("Hugging Face token for diarization")
        self.hf_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.hf_token_edit.setText(self.settings["hf_token"])
        diarization_layout.addRow("HF Token:", self.hf_token_edit)
        
        self.min_speakers_spin = QSpinBox()
        self.min_speakers_spin.setRange(0, 20)
        self.min_speakers_spin.setSpecialValueText("Auto")
        self.min_speakers_spin.setValue(0)
        diarization_layout.addRow("Min Speakers:", self.min_speakers_spin)
        
        self.max_speakers_spin = QSpinBox()
        self.max_speakers_spin.setRange(0, 20)
        self.max_speakers_spin.setSpecialValueText("Auto")
        self.max_speakers_spin.setValue(0)
        diarization_layout.addRow("Max Speakers:", self.max_speakers_spin)
        
        diarization_group.setLayout(diarization_layout)
        layout.addWidget(diarization_group)
        
        output_group = QGroupBox("Output")
        output_layout = QHBoxLayout()
        
        self.output_edit = QLineEdit()
        self.output_edit.setText(self.settings["output_dir"])
        output_layout.addWidget(QLabel("Directory:"))
        output_layout.addWidget(self.output_edit)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_output)
        output_layout.addWidget(self.browse_button)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def refresh_vocab_profiles(self):
        self.vocab_profile_combo.clear()
        profiles = self.vocab_processor.get_profile_names()
        if not profiles:
            self.vocab_processor.save_profile("default", {})
            profiles = ["default"]
        self.vocab_profile_combo.addItems(profiles)
        
    def on_preset_changed(self, preset):
        if preset == "Fast":
            self.model_combo.setCurrentText("medium")
            self.beam_spin.setValue(1)
            self.batch_spin.setValue(16)
            self.compute_combo.setCurrentText("int8")
        elif preset == "Balanced":
            self.model_combo.setCurrentText("large-v3")
            self.beam_spin.setValue(5)
            self.batch_spin.setValue(8)
            self.compute_combo.setCurrentText("int8")
        elif preset == "Accurate":
            self.model_combo.setCurrentText("large-v3")
            self.beam_spin.setValue(5)
            self.batch_spin.setValue(4)
            self.compute_combo.setCurrentText("int8")
            
    def browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_edit.setText(directory)
            
    def get_settings(self):
        min_speakers = self.min_speakers_spin.value() if self.min_speakers_spin.value() > 0 else None
        max_speakers = self.max_speakers_spin.value() if self.max_speakers_spin.value() > 0 else None
        
        return {
            "preset": self.preset_combo.currentText(),
            "model": self.model_combo.currentText(),
            "beam_size": self.beam_spin.value(),
            "batch_size": self.batch_spin.value(),
            "compute_type": self.compute_combo.currentText(),
            "output_dir": self.output_edit.text(),
            "enable_diarization": self.diarization_check.isChecked(),
            "hf_token": self.hf_token_edit.text(),
            "min_speakers": min_speakers,
            "max_speakers": max_speakers,
            "enable_vocabulary": self.vocab_check.isChecked(),
            "vocabulary_profile": self.vocab_profile_combo.currentText(),
            "vocabulary_threshold": self.vocab_threshold_spin.value()
        }
        
    def set_settings(self, settings):
        self.settings = settings
        self.preset_combo.setCurrentText(settings["preset"])
        self.model_combo.setCurrentText(settings["model"])
        self.beam_spin.setValue(settings["beam_size"])
        self.batch_spin.setValue(settings["batch_size"])
        self.compute_combo.setCurrentText(settings["compute_type"])
        self.output_edit.setText(settings["output_dir"])
        self.diarization_check.setChecked(settings["enable_diarization"])
        self.hf_token_edit.setText(settings["hf_token"])
        if settings["min_speakers"]:
            self.min_speakers_spin.setValue(settings["min_speakers"])
        if settings["max_speakers"]:
            self.max_speakers_spin.setValue(settings["max_speakers"])
        self.vocab_check.setChecked(settings.get("enable_vocabulary", False))
        if settings.get("vocabulary_profile"):
            self.vocab_profile_combo.setCurrentText(settings["vocabulary_profile"])
        self.vocab_threshold_spin.setValue(settings.get("vocabulary_threshold", 2))