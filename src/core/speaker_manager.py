from pathlib import Path
from typing import Dict, List, Optional, Union
import json
import torch
import numpy as np
from pyannote.audio import Inference
from pyannote.core import SlidingWindowFeature

class SpeakerProfile:
    def __init__(self, name: str, embedding: torch.Tensor, reference_path: str):
        self.name = name
        self.embedding = embedding
        self.reference_path = reference_path

class SpeakerManager:
    def __init__(self, profiles_dir: Optional[str] = None):
        if profiles_dir:
            self.profiles_dir = Path(profiles_dir)
        else:
            self.profiles_dir = Path.home() / "Library" / "Application Support" / "TranscriptionTool" / "speakers"
        
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, SpeakerProfile] = {}
        self.inference_model: Optional[Inference] = None
        
    def load_inference_model(self, hf_token: str):
        if self.inference_model is None:
            self.inference_model = Inference(
                "pyannote/embedding",
                use_auth_token=hf_token
            )
            
    def create_profile(self, name: str, audio_path: str, hf_token: str) -> bool:
        try:
            self.load_inference_model(hf_token)
            
            if self.inference_model is None:
                return False
            
            embedding_result = self.inference_model(audio_path)
            
            if isinstance(embedding_result, SlidingWindowFeature):
                embedding_array = embedding_result.data
                avg_embedding = torch.tensor(np.mean(embedding_array, axis=0))
            elif isinstance(embedding_result, np.ndarray):
                if len(embedding_result.shape) > 1:
                    avg_embedding = torch.tensor(np.mean(embedding_result, axis=0))
                else:
                    avg_embedding = torch.tensor(embedding_result)
            elif isinstance(embedding_result, torch.Tensor):
                if len(embedding_result.shape) > 1:
                    avg_embedding = embedding_result.mean(dim=0)
                else:
                    avg_embedding = embedding_result
            else:
                avg_embedding = torch.tensor(embedding_result)
            
            profile_data = {
                "name": name,
                "embedding": avg_embedding.tolist(),
                "reference_path": audio_path
            }
            
            profile_path = self.profiles_dir / f"{name}.json"
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f)
                
            self.profiles[name] = SpeakerProfile(
                name=name,
                embedding=avg_embedding,
                reference_path=audio_path
            )
            
            return True
        except Exception as e:
            print(f"Error creating speaker profile: {e}")
            return False
            
    def load_profiles(self):
        self.profiles.clear()
        
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    
                embedding = torch.tensor(data["embedding"])
                
                self.profiles[data["name"]] = SpeakerProfile(
                    name=data["name"],
                    embedding=embedding,
                    reference_path=data["reference_path"]
                )
            except Exception as e:
                print(f"Error loading profile {profile_file}: {e}")
                
    def get_profile(self, name: str) -> Optional[SpeakerProfile]:
        return self.profiles.get(name)
        
    def get_profile_names(self) -> List[str]:
        return list(self.profiles.keys())
        
    def delete_profile(self, name: str) -> bool:
        profile_path = self.profiles_dir / f"{name}.json"
        try:
            if profile_path.exists():
                profile_path.unlink()
            if name in self.profiles:
                del self.profiles[name]
            return True
        except Exception as e:
            print(f"Error deleting profile: {e}")
            return False
            
    def get_embeddings_dict(self) -> Dict[str, torch.Tensor]:
        return {name: profile.embedding for name, profile in self.profiles.items()}