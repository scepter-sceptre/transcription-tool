import whisperx
import torch
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from src.core.vocabulary_processor import VocabularyProcessor
from src.utils.logger import get_logger
import time

class Transcriber:
    def __init__(self, model_name: str = "large-v3", device: str = "cpu", compute_type: str = "int8"):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self.align_model = None
        self.align_metadata = None
        self.diarize_model = None
        self.beam_size = 5
        self.vocab_processor = VocabularyProcessor()
        self.logger = get_logger()
        
    def load_model(self, beam_size: int = 5):
        if self.model is None:
            self.beam_size = beam_size
            self.model = whisperx.load_model(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                language="en",
                asr_options={
                    "beam_size": beam_size,
                    "best_of": 5,
                    "patience": 1,
                    "length_penalty": 1,
                    "temperatures": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                }
            )
    
    def load_align_model(self):
        if self.align_model is None:
            self.align_model, self.align_metadata = whisperx.load_align_model(
                language_code="en",
                device=self.device
            )
    
    def load_diarize_model(self, hf_token: Optional[str] = None):
        if self.diarize_model is None and hf_token:
            from pyannote.audio import Pipeline
            self.diarize_model = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
            self.diarize_model.to(torch.device(self.device))
    
    def transcribe(
        self,
        audio_path: str,
        beam_size: int = 5,
        batch_size: int = 8,
        enable_diarization: bool = False,
        hf_token: Optional[str] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
        enable_vocabulary: bool = False,
        vocabulary_profile: str = "default",
        vocabulary_threshold: int = 2
    ) -> Dict[str, Any]:
        
        start_time = time.time()
        
        try:
            self.load_model(beam_size)
            assert self.model is not None
            
            audio = whisperx.load_audio(audio_path)
            
            result = self.model.transcribe(
                audio,
                batch_size=batch_size
            )
            
            self.load_align_model()
            assert self.align_model is not None
            assert self.align_metadata is not None
            result = whisperx.align(
                result["segments"],
                self.align_model,
                self.align_metadata,
                audio,
                self.device,
                return_char_alignments=False
            )
            
            if enable_diarization and hf_token:
                self.load_diarize_model(hf_token)
                assert self.diarize_model is not None
                diarize_segments = self.diarize_model(audio)
                result = whisperx.assign_word_speakers(diarize_segments, result)
            
            segments = []
            for seg in result["segments"]:
                words = seg.get("words", [])
                if words:
                    scores = [float(w.get("score", 0.0)) for w in words if "score" in w]
                    avg_confidence = sum(scores) / len(scores) if scores else 0.0
                else:
                    avg_confidence = 0.0
                
                segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip(),
                    "speaker": seg.get("speaker", None),
                    "confidence": avg_confidence
                })
            
            if enable_vocabulary:
                segments = self.vocab_processor.apply_vocabulary(
                    segments,
                    vocabulary_profile,
                    vocabulary_threshold
                )
            
            duration = len(audio) / 16000.0
            processing_time = time.time() - start_time
            
            self.logger.log_performance({
                "file": str(Path(audio_path).name),
                "model": self.model_name,
                "audio_duration": duration,
                "processing_time": processing_time,
                "ratio": processing_time / duration if duration > 0 else 0,
                "beam_size": beam_size,
                "batch_size": batch_size,
                "diarization": enable_diarization,
                "vocabulary": enable_vocabulary,
                "segments_count": len(segments)
            })
            
            self.logger.log_session({
                "file": str(Path(audio_path).name),
                "model": self.model_name,
                "duration": duration,
                "segments": len(segments),
                "diarization": enable_diarization,
                "vocabulary_applied": enable_vocabulary
            })
            
            output = {
                "metadata": {
                    "source_file": str(Path(audio_path).name),
                    "duration": duration,
                    "model": self.model_name,
                    "diarization_enabled": enable_diarization,
                    "vocabulary_applied": enable_vocabulary,
                    "processing_preset": "custom",
                    "parameters": {
                        "beam_size": self.beam_size,
                        "compute_type": self.compute_type,
                        "batch_size": batch_size
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                "segments": segments
            }
            
            return output
            
        except Exception as e:
            self.logger.log_error(
                "TranscriptionError",
                str(e),
                {
                    "file": str(Path(audio_path).name),
                    "model": self.model_name,
                    "beam_size": beam_size
                }
            )
            raise
    
    def save_transcript(self, transcript: Dict[str, Any], output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)
    
    def unload_model(self):
        if self.model is not None:
            del self.model
            self.model = None
        if self.align_model is not None:
            del self.align_model
            self.align_model = None
        if self.diarize_model is not None:
            del self.diarize_model
            self.diarize_model = None
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()