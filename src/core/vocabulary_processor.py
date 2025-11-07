from pathlib import Path
from typing import Dict, List, Optional
import json
from Levenshtein import distance as levenshtein_distance

class VocabularyProfile:
    def __init__(self, name: str, terms: Dict[str, str]):
        self.name = name
        self.terms = terms
        
class VocabularyProcessor:
    def __init__(self, vocab_dir: Optional[str] = None):
        if vocab_dir:
            self.vocab_dir = Path(vocab_dir)
        else:
            self.vocab_dir = Path.home() / "Library" / "Application Support" / "TranscriptionTool" / "vocabularies"
        
        self.vocab_dir.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, VocabularyProfile] = {}
        self.load_profiles()
        
    def load_profiles(self):
        for vocab_file in self.vocab_dir.glob("*.json"):
            try:
                with open(vocab_file, 'r', encoding='utf-8') as f:
                    terms = json.load(f)
                profile_name = vocab_file.stem
                self.profiles[profile_name] = VocabularyProfile(profile_name, terms)
            except Exception as e:
                print(f"Error loading vocabulary {vocab_file}: {e}")
                
    def save_profile(self, profile_name: str, terms: Dict[str, str]):
        profile_path = self.vocab_dir / f"{profile_name}.json"
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(terms, f, indent=2, ensure_ascii=False)
            self.profiles[profile_name] = VocabularyProfile(profile_name, terms)
            return True
        except Exception as e:
            print(f"Error saving vocabulary: {e}")
            return False
            
    def delete_profile(self, profile_name: str) -> bool:
        profile_path = self.vocab_dir / f"{profile_name}.json"
        try:
            if profile_path.exists():
                profile_path.unlink()
            if profile_name in self.profiles:
                del self.profiles[profile_name]
            return True
        except Exception as e:
            print(f"Error deleting vocabulary: {e}")
            return False
            
    def get_profile(self, profile_name: str) -> Optional[VocabularyProfile]:
        return self.profiles.get(profile_name)
        
    def get_profile_names(self) -> List[str]:
        return list(self.profiles.keys())
        
    def apply_vocabulary(
        self, 
        segments: List[Dict], 
        profile_name: str, 
        threshold: int = 2
    ) -> List[Dict]:
        profile = self.get_profile(profile_name)
        if not profile or not profile.terms:
            return segments
            
        processed_segments = []
        for segment in segments:
            text = segment["text"]
            words = text.split()
            
            for i, word in enumerate(words):
                word_clean = word.strip('.,!?;:"\'-').lower()
                
                for phonetic, correct in profile.terms.items():
                    phonetic_lower = phonetic.lower()
                    
                    if word_clean == phonetic_lower:
                        words[i] = word.replace(word_clean, correct, 1)
                        break
                    elif levenshtein_distance(word_clean, phonetic_lower) <= threshold:
                        words[i] = word.replace(word_clean, correct, 1)
                        break
                        
            segment["text"] = " ".join(words)
            processed_segments.append(segment)
            
        return processed_segments
        
    def export_profile(self, profile_name: str, export_path: str) -> bool:
        profile = self.get_profile(profile_name)
        if not profile:
            return False
            
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(profile.terms, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting vocabulary: {e}")
            return False
            
    def import_profile(self, profile_name: str, import_path: str) -> bool:
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                terms = json.load(f)
            return self.save_profile(profile_name, terms)
        except Exception as e:
            print(f"Error importing vocabulary: {e}")
            return False