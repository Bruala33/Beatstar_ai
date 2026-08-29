import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import scipy.signal
import librosa

from app.config import settings

logger = logging.getLogger(__name__)

class AudioAnalyzer:
    """
    High-sensitivity percussive & harmonic audio analyzer using Librosa:
    HPSS separation, high-precision percussive onset peak picking, and long sustained vocal detection.
    """

    def __init__(self, sr: int = settings.SAMPLE_RATE, hop_length: int = settings.HOP_LENGTH):
        self.sr = sr
        self.hop_length = hop_length

    def _butter_filter(self, data: np.ndarray, cutoff: float or Tuple[float, float], btype: str, order: int = 4) -> np.ndarray:
        nyq = 0.5 * self.sr
        if isinstance(cutoff, (list, tuple)):
            normal_cutoff = [c / nyq for c in cutoff]
        else:
            normal_cutoff = cutoff / nyq
            
        b, a = scipy.signal.butter(order, normal_cutoff, btype=btype, analog=False)
        return scipy.signal.filtfilt(b, a, data)

    def separate_bands(self, y: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Splits audio waveform into frequency bands:
        - Bass: < 200 Hz (kicks, sub-bass, rhythm backbone)
        - Mid: 300 Hz - 3000 Hz (snare fundamental, vocals, lead synths, chords)
        - High: > 3000 Hz (cymbals, hi-hats, airy percussive transients)
        """
        bass = self._butter_filter(y, settings.BASS_CUTOFF_HZ, btype='lowpass')
        mid = self._butter_filter(y, (settings.MID_LOW_HZ, settings.MID_HIGH_HZ), btype='bandpass')
        high = self._butter_filter(y, settings.MID_HIGH_HZ, btype='highpass')
        
        return {
            "bass": bass,
            "mid": mid,
            "high": high
        }

    def analyze(self, y: np.ndarray, onset_sensitivity: float = 1.0) -> Dict[str, Any]:
        """
        Performs high-sensitivity percussive audio analysis with strict sustained vocal detection.
        """
        logger.info("Separating harmonic and percussive stems (HPSS)...")
        y_harmonic, y_percussive = librosa.effects.hpss(y)

        bands = self.separate_bands(y)

        # 1. Precise Beat Tracking
        logger.info("Estimating BPM and beat grid...")
        tempo_val, beat_frames = librosa.beat.beat_track(
            y=y_percussive,
            sr=self.sr,
            hop_length=self.hop_length,
            tightness=100
        )
        
        bpm = float(tempo_val[0]) if isinstance(tempo_val, (np.ndarray, list)) else float(tempo_val)
        if bpm < 50:
            bpm = 120.0
        elif bpm > 190:
            bpm = bpm / 2.0

        beat_times = librosa.frames_to_time(beat_frames, sr=self.sr, hop_length=self.hop_length)
        beat_times_ms = [int(t * 1000) for t in beat_times]

        # 2. High-Sensitivity Percussive Onset Detection
        logger.info("Extracting percussive onsets and transients...")
        onset_env_perc = librosa.onset.onset_strength(y=y_percussive, sr=self.sr, hop_length=self.hop_length)
        onset_env_bass = librosa.onset.onset_strength(y=bands["bass"], sr=self.sr, hop_length=self.hop_length)
        onset_env_harm = librosa.onset.onset_strength(y=y_harmonic, sr=self.sr, hop_length=self.hop_length)

        onset_env_combined = 0.70 * onset_env_perc + 0.20 * onset_env_bass + 0.10 * onset_env_harm

        sens_factor = max(0.4, min(2.5, onset_sensitivity))
        delta_perc = 0.065 / sens_factor

        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env_combined,
            sr=self.sr,
            hop_length=self.hop_length,
            backtrack=True,
            delta=delta_perc,
            wait=3  # ~70ms spacing
        )

        rms_total = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
        rms_harm = librosa.feature.rms(y=y_harmonic, hop_length=self.hop_length)[0]
        rms_bass = librosa.feature.rms(y=bands["bass"], hop_length=self.hop_length)[0]
        rms_mid = librosa.feature.rms(y=bands["mid"], hop_length=self.hop_length)[0]
        rms_high = librosa.feature.rms(y=bands["high"], hop_length=self.hop_length)[0]
        
        spectral_centroid = librosa.feature.spectral_centroid(
            y=y, sr=self.sr, hop_length=self.hop_length
        )[0]

        max_rms = np.max(rms_total) if len(rms_total) > 0 and np.max(rms_total) > 0 else 1.0
        swipe_cutoff = np.percentile(onset_env_combined, settings.SWIPE_ENERGY_PERCENTILE) if len(onset_env_combined) > 0 else 1.0

        detected_onsets = []
        for frame in onset_frames:
            if frame >= len(rms_total):
                continue

            time_sec = librosa.frames_to_time(frame, sr=self.sr, hop_length=self.hop_length)
            time_ms = int(time_sec * 1000)

            env_val = float(onset_env_combined[frame])
            norm_energy = float(min(1.0, rms_total[frame] / max_rms))

            if norm_energy < 0.06 and env_val < 0.12:
                continue

            bass_e = rms_bass[frame] if frame < len(rms_bass) else 0
            mid_e = rms_mid[frame] if frame < len(rms_mid) else 0
            high_e = rms_high[frame] if frame < len(rms_high) else 0

            if bass_e >= mid_e and bass_e >= high_e:
                dominant_band = "bass"
            elif high_e > mid_e and high_e > bass_e:
                dominant_band = "high"
            else:
                dominant_band = "mid"

            centroid_val = float(spectral_centroid[frame]) if frame < len(spectral_centroid) else 1000.0

            # Strict long vocal/synth sustain check (>= 700 ms only)
            is_sustained = False
            sustain_duration_ms = 0
            
            harm_onset_e = rms_harm[frame] if frame < len(rms_harm) else 0
            if harm_onset_e > 0.04 and (dominant_band == "mid" or dominant_band == "bass"):
                sustain_frames = 0
                max_sustain_frames = int((settings.MAX_HOLD_DURATION_MS / 1000.0) * (self.sr / self.hop_length))
                
                for f_next in range(frame + 1, min(len(rms_harm), frame + max_sustain_frames)):
                    # Must maintain at least 60% of harmonic energy throughout
                    if rms_harm[f_next] < harm_onset_e * 0.60 or (f_next in onset_frames and onset_env_combined[f_next] > env_val * 0.90):
                        break
                    sustain_frames += 1

                sustain_time_ms = int(sustain_frames * (self.hop_length / self.sr) * 1000)
                if sustain_time_ms >= settings.MIN_HOLD_DURATION_MS:
                    is_sustained = True
                    sustain_duration_ms = min(sustain_time_ms, settings.MAX_HOLD_DURATION_MS)

            is_swipe_candidate = (env_val >= swipe_cutoff and norm_energy > 0.48)

            detected_onsets.append({
                "frame": int(frame),
                "timestamp_ms": time_ms,
                "energy": norm_energy,
                "onset_strength": env_val,
                "band": dominant_band,
                "centroid": centroid_val,
                "is_sustained": is_sustained,
                "sustain_duration_ms": sustain_duration_ms,
                "is_swipe_candidate": is_swipe_candidate
            })

        logger.info(f"Analysis completed: BPM={bpm:.1f}, Onsets={len(detected_onsets)}, Long holds={sum(1 for o in detected_onsets if o['is_sustained'])}")
        return {
            "bpm": round(bpm, 2),
            "beat_times_ms": beat_times_ms,
            "onsets": detected_onsets
        }
