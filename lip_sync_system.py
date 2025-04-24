from typing import List, Dict, Optional, Union, Tuple
import json
import os
import re
import subprocess
import tempfile

class LipSyncSystem:
    def __init__(self, static_map_path: str = "static_viseme_map.json"):
        self.static_map = self._load_static_map(static_map_path)
        self.mode = "simple"
        self.rhubarb_path = ""
        self.transition_weights = self._initialize_transition_weights()
        
    def _load_static_map(self, map_path: str) -> Dict[str, str]:
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading static map: {e}")
            return {}
            
    def _initialize_transition_weights(self) -> Dict[str, Dict[str, float]]:
        visemes = list(set(self.static_map.values()))
        weights = {v1: {v2: 1.0 for v2 in visemes} for v1 in visemes}
        
        common_transitions = [
            ("PP", "AA", 2.0),
            ("PP", "EE", 2.0),
            ("KK", "AA", 1.8),
            ("DD", "EE", 1.8),
            ("SS", "DD", 1.5),
            ("TH", "EE", 1.5),
            ("NN", "DD", 1.7),
            ("AX", "NN", 1.6),
        ]
        
        for src, dst, weight in common_transitions:
            if src in weights and dst in weights[src]:
                weights[src][dst] = weight
                
        return weights
        
    def set_mode(self, mode: str) -> None:
        valid_modes = ["simple", "predictive", "rhubarb"]
        if mode not in valid_modes:
            raise ValueError(f"Mode must be one of {valid_modes}")
        
        if mode == "rhubarb" and not self.rhubarb_path:
            print("Warning: Rhubarb mode selected but Rhubarb path not set")
            
        self.mode = mode
        print(f"Lip sync mode set to: {mode}")
        
    def set_rhubarb_path(self, path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Rhubarb executable not found at: {path}")
        self.rhubarb_path = path
        print(f"Rhubarb path set to: {path}")
        
    def process_phonemes(self, phonemes: List[str]) -> List[str]:
        if self.mode == "simple":
            return self._simple_mapping(phonemes)
        elif self.mode == "predictive":
            return self._predictive_mapping(phonemes)
        elif self.mode == "rhubarb":
            raise ValueError("For Rhubarb mode, use process_audio_file() instead")
        
    def _simple_mapping(self, phonemes: List[str]) -> List[str]:
        visemes = []
        for p in phonemes:
            viseme = self.static_map.get(p, "sil")
            visemes.append(viseme)
        return visemes
    
    def _predictive_mapping(self, phonemes: List[str]) -> List[str]:
        basic_visemes = self._simple_mapping(phonemes)
        smoothed_visemes = []
        prev_viseme = "sil"
        
        for i, viseme in enumerate(basic_visemes):
            if viseme == prev_viseme and i > 0:
                if i < len(basic_visemes) - 1:
                    next_viseme = basic_visemes[i + 1]
                    transition_weight = self.transition_weights.get(prev_viseme, {}).get(next_viseme, 1.0)
                    if transition_weight > 1.5:
                        continue
            
            smoothed_visemes.append(viseme)
            prev_viseme = viseme
            
        return smoothed_visemes
        
    def process_audio_file(self, audio_path: str, output_path: Optional[str] = None) -> List[Tuple[float, str]]:
        if self.mode == "rhubarb":
            return self._process_with_rhubarb(audio_path, output_path)
        else:
            raise NotImplementedError("Audio file processing requires Rhubarb mode or external phoneme extraction")
            
    def _process_with_rhubarb(self, audio_path: str, output_path: Optional[str] = None) -> List[Tuple[float, str]]:
        if not self.rhubarb_path:
            raise ValueError("Rhubarb path not set. Use set_rhubarb_path() first.")
            
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        if not output_path:
            output_path = os.path.splitext(audio_path)[0] + ".txt"
            
        cmd = [
            self.rhubarb_path,
            "-o", output_path,
            "--exportFormat", "txt",
            audio_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            viseme_data = []
            with open(output_path, 'r') as f:
                for line in f:
                    match = re.match(r'(\d+\.\d+)\s+(\w+)', line.strip())
                    if match:
                        timestamp = float(match.group(1))
                        viseme = match.group(2)
                        viseme_data.append((timestamp, viseme))
            
            return viseme_data
            
        except subprocess.CalledProcessError as e:
            print(f"Rhubarb process error: {e}")
            print(f"Stdout: {e.stdout.decode('utf-8')}")
            print(f"Stderr: {e.stderr.decode('utf-8')}")
            return []
        except Exception as e:
            print(f"Error in Rhubarb processing: {e}")
            return []
            
    def convert_phoneme_sequence(self, text: str) -> List[str]:
        phonemes = []
        i = 0
        while i < len(text):
            if i < len(text) - 1 and text[i:i+2] in ['ʧ', 'ʤ', 'ŋ']:
                phonemes.append(text[i:i+2])
                i += 2
            else:
                phonemes.append(text[i])
                i += 1
        return phonemes
    
    def generate_phoneme_timing(self, text: str) -> List[Dict[str, Union[str, float]]]:
        phonemes = []
        words = text.split()
        current_time = 0.0
        
        for word in words:
            if not word:
                continue
                
            # Simple simulation of phoneme extraction
            # In a real implementation, you would use a proper phoneme extraction library
            word_phoneme_map = {
                "hello": [{"phoneme": "HH", "duration": 0.1}, 
                          {"phoneme": "EH", "duration": 0.1}, 
                          {"phoneme": "L", "duration": 0.1}, 
                          {"phoneme": "OW", "duration": 0.1}],
                "how": [{"phoneme": "HH", "duration": 0.1}, 
                        {"phoneme": "AW", "duration": 0.1}],
                "are": [{"phoneme": "AA", "duration": 0.1}, 
                        {"phoneme": "R", "duration": 0.1}],
                "you": [{"phoneme": "Y", "duration": 0.1}, 
                       {"phoneme": "UW", "duration": 0.1}]
            }
            
            # Get phonemes for this word, or use a default approach
            word_phonemes = word_phoneme_map.get(word.lower().strip(".,!?"), [])
            
            if not word_phonemes:
                # Fallback: create a simple phoneme for each character
                for char in word:
                    phonemes.append({
                        "phoneme": char.upper(),
                        "start": current_time,
                        "end": current_time + 0.1
                    })
                    current_time += 0.1
            else:
                # Add the mapped phonemes with timing
                for p in word_phonemes:
                    phonemes.append({
                        "phoneme": p["phoneme"],
                        "start": current_time,
                        "end": current_time + p["duration"]
                    })
                    current_time += p["duration"]
            
            # Add a small gap between words
            current_time += 0.1
                
        return phonemes