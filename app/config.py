import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Beatstar Beatmap Generator API"
    VERSION: str = "1.2.0"
    API_V1_STR: str = "/api/v1"
    
    # Audio Analysis Defaults
    SAMPLE_RATE: int = 22050
    HOP_LENGTH: int = 512
    N_FFT: int = 2048
    MAX_DURATION_SECONDS: int = 600  # 10 minutes max
    
    # Frequency bands for separation (Hz)
    BASS_CUTOFF_HZ: float = 200.0       # Low frequency (<200Hz for rhythm, kicks, bass)
    MID_LOW_HZ: float = 300.0           # Mid/vocal lower bound (300Hz)
    MID_HIGH_HZ: float = 3000.0         # Mid/vocal upper bound (3000Hz)
    
    # Beatmap Generation Settings
    NUM_LANES: int = 3
    MIN_NOTE_GAP_MS: int = 120          # Minimum time between notes
    MIN_HOLD_DURATION_MS: int = 700     # Minimum duration for a true hold note (>=700ms, strictly long vocals/chords)
    MAX_HOLD_DURATION_MS: int = 2800    # Maximum duration for a single hold note
    SWIPE_ENERGY_PERCENTILE: float = 88.0 # Top % of transient energy that triggers a 'swipe'
    
    # Difficulty Presets (multiplier for note density)
    DIFFICULTY_THRESHOLDS: dict = {
        "easy": {"onset_delta": 0.22, "max_notes_per_second": 2.2},
        "normal": {"onset_delta": 0.12, "max_notes_per_second": 3.8},
        "hard": {"onset_delta": 0.07, "max_notes_per_second": 5.5},
        "expert": {"onset_delta": 0.04, "max_notes_per_second": 7.1},
    }

settings = Settings()
