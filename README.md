# Transcription Tool PRD

## Overview
Desktop application for transcribing audio and video files using WhisperX on macOS (M3 Max, 36GB RAM). Single-user tool optimized for accuracy and speed with real-time preview.

## Target User
Developer with M3 Max MacBook Pro requiring accurate English transcription with speaker diarization.

## Core Requirements

### Model
- Primary: WhisperX (supports diarization)
- In-app model download and management
- Model selection UI for different sizes: tiny, base, small, medium, large-v2, large-v3
- Model size as primary speed control

### Input
- Drag and drop files onto application window
- File picker dialog
- Supported formats: MP3, WAV, M4A, MP4, MOV, AVI, MKV

### Processing
- Batch processing queue
- Real-time transcription preview in side panel during processing
- Optional speaker diarization toggle
- Queue management (pause, cancel, reorder)
- Language hardcoded to English for optimal performance

### Output
- JSON export format
- Configurable output directory
- Filename pattern: `{original_filename}_transcript.json`

### JSON Schema
```json
{
  "metadata": {
    "source_file": "string",
    "duration": "float",
    "model": "string",
    "diarization_enabled": "boolean",
    "vocabulary_applied": "boolean",
    "processing_preset": "string",
    "parameters": {
      "beam_size": "int",
      "compute_type": "string",
      "batch_size": "int"
    },
    "timestamp": "ISO8601"
  },
  "segments": [
    {
      "start": "float",
      "end": "float",
      "text": "string",
      "speaker": "string|null",
      "confidence": "float"
    }
  ]
}
```

## Technical Specifications

### Hardware Optimization
- M3 Max Metal Performance Shaders (MPS) utilization
- 36GB RAM capacity management
- Multi-threaded processing for batch queue
- GPU acceleration via Metal
- Pin to performance cores during processing
- fp16 compute for all operations

### Dependencies
- WhisperX
- PyTorch with MPS backend
- Python 3.11+
- ffmpeg for media processing
- pyannote.audio (diarization)

### Platform
- macOS 15.4.1+
- Native Apple Silicon binary

## Performance Optimizations

### Model Selection Performance
- `tiny`: ~75MB, ~1min/hour, highest WER
- `base`: ~140MB, ~2min/hour
- `small`: ~460MB, ~4min/hour
- `medium`: ~1.5GB, ~6-8min/hour, ~2% WER vs large
- `large-v2/v3`: ~3GB, ~15-20min/hour (beam=5), best accuracy

### Beam Size Impact
- `beam_size=1` (greedy): ~6-8min/hour, 2-5% higher WER
- `beam_size=5` (default): ~15-20min/hour, baseline accuracy
- `beam_size=10`: ~25-30min/hour, <1% WER improvement

### Audio Preprocessing
- Convert to 16kHz mono before transcription
- Strip video streams immediately for video files
- Cache Voice Activity Detection results

### Pipeline Optimization
- Parallel diarization during alignment phase
- Clear model from VRAM between queue items
- Batch similar files with same settings

### Processing Presets

**Fast:**
- Model: medium
- Beam: 1
- Batch: 16
- Compute: float16
- Target: ~6-8min/hour

**Balanced:**
- Model: large-v3
- Beam: 5
- Batch: 8
- Compute: float16
- Target: ~15-20min/hour

**Accurate:**
- Model: large-v3
- Beam: 5
- Batch: 4
- Compute: float32
- Target: ~20-25min/hour

### Advanced Parameters (Settings Dialog)
- `beam_size`: 1, 5, 10
- `compute_type`: float16, float32
- `batch_size`: 4, 8, 16
- `condition_on_previous_text`: Boolean (default: True)
- `vad_filter`: Boolean (default: True)
- `no_speech_threshold`: 0.0-1.0 (default: 0.6)
- `logprob_threshold`: Float (default: -1.0)
- `compression_ratio_threshold`: Float (default: 2.4)

### Diarization Parameters
- `min_speakers`: Int (optional)
- `max_speakers`: Int (optional)
- `num_speakers`: Int (optional, exact count if known)

## Functional Requirements

### Model Management
- Download models from within app
- Display available models with size, speed estimate, and accuracy info
- Delete unused models to free storage
- Default model selection persistence
- Hugging Face token input in settings for diarization models

### Processing Queue
- Visual queue list showing:
  - Filename
  - Status (queued/processing/complete/error)
  - Progress percentage
  - Estimated time remaining
  - Preset used
- Batch operations: add multiple files, clear completed

### Real-time Preview
- Side panel displays transcription as it generates
- Auto-scroll to latest segment
- Segment timestamps visible
- Speaker labels if diarization enabled

### Error Handling
- Clear error messages for:
  - Unsupported file formats
  - Corrupted files
  - Insufficient storage
  - Model download failures
  - Missing Hugging Face token
- Failed items remain in queue for retry

### Custom Vocabulary
- User-defined term dictionary for improved accuracy
- JSON format: `{"phonetic_match": "Correct Term"}`
- Post-processing with fuzzy matching (Levenshtein distance threshold)
- Forced alignment for low-confidence segments
- In-app vocabulary editor:
  - Add/remove terms
  - Import/export vocabulary JSON
  - Per-transcription toggle
  - Applied during batch processing
- Use cases: technical jargon, proper nouns, acronyms, domain-specific terminology
- Vocabulary file stored in app preferences directory
- Multiple vocabulary profiles (default, project-specific)

## UI/UX Requirements

### Design Principles
- Minimal, functional, utilitarian
- No animations
- No marketing copy or branding elements
- Efficient use of screen space

### Layout
```
+--------------------------------------------------+
|  [Preset: Balanced ▼] [Model: large-v3 ▼] [⚙️]  |
+--------------------------------------------------+
|                    |                             |
|   Processing       |   Preview                   |
|   Queue            |                             |
|   (60%)            |   (40%)                     |
|                    |                             |
|   • file1.mp4      |   [00:01:23]               |
|     Processing     |   Speaker 1:               |
|     45% (~8min)    |   "Lorem ipsum..."         |
|                    |                             |
|   • file2.wav      |   [00:01:45]               |
|     Queued         |   Speaker 2:               |
|     (Fast/medium)  |   "Dolor sit..."           |
|                    |                             |
+--------------------------------------------------+
|  [+ Add Files] [Clear Done]  870GB Free         |
+--------------------------------------------------+
```

### Controls
- Preset selector dropdown (Fast/Balanced/Accurate)
- Model selector dropdown
- Settings button (⚙️) for:
  - Advanced parameters
  - Diarization toggle and speaker constraints
  - Output directory
  - Hugging Face token
  - Vocabulary management
  - Vocabulary profile selection
- Add files button
- Clear completed button
- Per-item cancel button

### Vocabulary Editor
- Table view with columns: Match Term | Replacement | Actions
- Add/remove rows
- Import JSON button
- Export JSON button
- Fuzzy match threshold slider
- Profile selector/creator

### Visual Feedback
- Progress bars for active transcriptions
- Status indicators (color-coded text only)
- Estimated time remaining per item
- Storage remaining display
- Vocabulary applied indicator on completed items
- Preset/model displayed per queue item

## Performance Requirements

### Speed Targets
- 1 hour audio processes per preset targets above
- Batch queue processes sequentially without UI blocking
- Model loading <5 seconds
- Vocabulary post-processing adds <2% overhead

### Accuracy
- Word Error Rate (WER) <5% for clear English audio (large model)
- Diarization accuracy >90% for distinct speakers
- Custom vocabulary replacement accuracy >95% for matched terms

### Resource Usage
- Max 32GB RAM usage during processing
- Efficient thermal management (no throttling)
- Background processing priority below user tasks
- Clear VRAM between queue items

## Storage Requirements

### Models
- Support for multiple model sizes (see Model Selection Performance)
- Display storage impact before download
- Allow multiple models installed simultaneously

### Output Files
- JSON files typically <1% of source media size
- Temporary files cleaned after processing
- Vocabulary files <100KB each

### Vocabulary Storage
- Default location: `~/Library/Application Support/TranscriptionTool/vocabularies/`
- Per-profile JSON files
- Backup/sync capability via export

## Success Metrics
- Processing speed matches preset targets
- Transcription accuracy (WER <5% for large model)
- Vocabulary replacement accuracy and coverage
- User time from file selection to usable JSON output
- Application stability (zero crashes during normal operation)

## Future Considerations
- API for programmatic access
- Vocabulary sharing/importing from community sources
- Custom preset creation and management


# Transcription Tool

Desktop application for transcribing audio and video files using WhisperX on macOS.

## Features

- Batch processing queue for multiple files
- Multiple Whisper models (tiny → large-v3)
- Speaker diarization
- Custom vocabulary for domain-specific accuracy
- Model management (download/delete)
- Processing presets (Fast/Balanced/Accurate)

## Requirements

- macOS 15.4.1+
- Python 3.11-3.13
- Poetry
- 36GB RAM recommended for large models

## Installation
```bash
# Install Poetry
brew install poetry

# Clone repository
git clone <your-repo-url>
cd transcription-tool

# Install dependencies
poetry install

# Run application
poetry run python -m src.main
```

## Usage

1. Click "Models" to download desired Whisper model
2. Add audio/video files to queue
3. Configure settings (preset, diarization, vocabulary)
4. Click "Start Processing"
5. Transcripts saved to `outputs/` directory

## Configuration

- **Presets:**
  - Fast: medium model, beam=1 (~6-8min/hour)
  - Balanced: large-v3, beam=5 (~15-20min/hour)
  - Accurate: large-v3, beam=5, float32 (~20-25min/hour)

- **Diarization:** Requires Hugging Face token
- **Vocabulary:** Custom term replacement with fuzzy matching

## Development
```bash
# Run tests
poetry run python -m test.test_transcribe

# Project structure
src/
├── main.py              # Entry point
├── ui/                  # PyQt6 interface
├── core/                # Transcription engine
└── utils/               # Configuration
```

