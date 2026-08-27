import random
import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models.beatmap import (
    BeatstarNote,
    BeatmapMetadata,
    BeatmapResponse,
    NoteType,
    SwipeDirection,
    DifficultyLevel
)

logger = logging.getLogger(__name__)

class BeatmapGenerator:
    """
    Transforms acoustic transients into a high-octane, percussive Beatstar beatmap
    with 5-second clean intro margin, musical beat quantization, 2-thumb limit, and lateral-only hold notes.
    """

    @staticmethod
    def _quantize_to_musical_grid(timestamp_ms: int, bpm: float, allow_16ths: bool = True, quarters_only: bool = False) -> int:
        """
        Snaps a timestamp to the closest musical sub-beat division:
        - 1/1 Beat (Quarter note / Negra)
        - 1/2 Beat (Eighth note / Corchea)
        - 1/4 Beat (Sixteenth note / Semicorchea)
        - 1/3 Beat (Triplet / Tresillo)
        """
        if bpm <= 0:
            return timestamp_ms

        beat_ms = 60000.0 / bpm
        
        if quarters_only:
            subdivisions = [beat_ms]
        elif not allow_16ths:
            subdivisions = [beat_ms, beat_ms / 2.0, beat_ms / 3.0]
        else:
            subdivisions = [beat_ms, beat_ms / 2.0, beat_ms / 3.0, beat_ms / 4.0]

        best_snapped = timestamp_ms
        min_diff = 80.0

        for sub in subdivisions:
            index = round(timestamp_ms / sub)
            grid_time = int(index * sub)
            diff = abs(timestamp_ms - grid_time)
            if diff < min_diff:
                min_diff = diff
                best_snapped = grid_time

        return max(0, best_snapped)

    @classmethod
    def generate(
        cls,
        analysis: Dict[str, Any],
        metadata: Dict[str, Any],
        difficulty: DifficultyLevel = "normal",
        snap_to_grid: bool = True
    ) -> BeatmapResponse:
        """
        Generates percussive 3-lane Beatstar beatmap with real difficulty scaling,
        curated low-frequency directional swipe notes, and 5000ms (5s) clean intro buffer.
        """
        bpm = analysis.get("bpm", 120.0)
        raw_onsets = analysis.get("onsets", [])
        song_duration = metadata.get("duration", 0.0)

        # 1. Real Difficulty Parameters
        if difficulty == "easy":
            scroll_duration_ms = 1800
            quarters_only = True
            allow_16ths = False
            energy_threshold = 0.24
            min_global_gap_ms = 320
            min_lane_gap_ms = 380
            allow_swipes = False
            swipe_chance = 0.0
        elif difficulty == "normal":
            scroll_duration_ms = 1400
            quarters_only = False
            allow_16ths = False
            energy_threshold = 0.12
            min_global_gap_ms = 160
            min_lane_gap_ms = 200
            allow_swipes = True
            swipe_chance = 0.04  # Low frequency for key moments
        elif difficulty == "hard":
            scroll_duration_ms = 950
            quarters_only = False
            allow_16ths = True
            energy_threshold = 0.06
            min_global_gap_ms = 95
            min_lane_gap_ms = 125
            allow_swipes = True
            swipe_chance = 0.07  # Occasional key swipe
        else: # expert
            scroll_duration_ms = 800
            quarters_only = False
            allow_16ths = True
            energy_threshold = 0.03
            min_global_gap_ms = 70
            min_lane_gap_ms = 90
            allow_swipes = True
            swipe_chance = 0.10

        # 5.0 Seconds (5000ms) Intro Margin Filter
        INTRO_MARGIN_MS = 5000

        filtered_onsets = []
        last_t = -99999

        for item in raw_onsets:
            t = item["timestamp_ms"]
            energy = item["energy"]

            # Filter out all notes occurring during the first 5 seconds
            if t < INTRO_MARGIN_MS:
                continue
            
            if energy < energy_threshold:
                continue

            snapped_t = cls._quantize_to_musical_grid(
                t, bpm, allow_16ths=allow_16ths, quarters_only=quarters_only
            ) if snap_to_grid else t

            if snapped_t < INTRO_MARGIN_MS:
                continue

            if (snapped_t - last_t) >= min_global_gap_ms:
                item_copy = dict(item)
                item_copy["timestamp_ms"] = snapped_t
                filtered_onsets.append(item_copy)
                last_t = snapped_t

        notes: List[BeatstarNote] = []
        lanes: List[List[BeatstarNote]] = [[], [], []]

        lane_busy_until = [0, 0, 0]
        active_hold_end = 0
        active_hold_lane = -1
        last_tap_during_hold_t = -99999
        last_swipe_t = -99999
        last_lane = 1
        thumb_turn = 0
        note_id_counter = 1

        for onset in filtered_onsets:
            t = onset["timestamp_ms"]
            band = onset.get("band", "mid")
            centroid = onset.get("centroid", 1000.0)
            is_sustained = onset.get("is_sustained", False)
            sustain_duration_ms = onset.get("sustain_duration_ms", 0)
            energy = onset.get("energy", 0.5)

            is_hold_active = (t < active_hold_end)

            # Strict 2-finger limit during hold notes
            if is_hold_active:
                if (t - last_tap_during_hold_t) < 220:
                    continue
                is_sustained = False

            # Lateral-only Hold Rule: Holds can NEVER be in Lane 1 (Center)
            can_be_hold = (
                is_sustained and 
                sustain_duration_ms >= settings.MIN_HOLD_DURATION_MS and 
                not is_hold_active and
                (difficulty != "easy" or sustain_duration_ms >= 1000)
            )

            if can_be_hold:
                lateral_lanes = [0, 2] if thumb_turn == 0 else [2, 0]
                chosen_lane = None
                for cand_lane in lateral_lanes:
                    if t >= lane_busy_until[cand_lane] + min_lane_gap_ms:
                        chosen_lane = cand_lane
                        break

                if chosen_lane is not None:
                    note_type: NoteType = "hold"
                    duration_ms = sustain_duration_ms
                    end_timestamp_ms = t + duration_ms
                    lane_busy_until[chosen_lane] = end_timestamp_ms + min_lane_gap_ms
                    active_hold_end = end_timestamp_ms
                    active_hold_lane = chosen_lane
                    thumb_turn = 1 - thumb_turn

                    note = BeatstarNote(
                        id=note_id_counter,
                        lane=chosen_lane,
                        type=note_type,
                        timestamp_ms=t,
                        duration_ms=duration_ms,
                        end_timestamp_ms=end_timestamp_ms,
                        direction=None,
                        frequency_band=band,
                        energy=round(energy, 3)
                    )
                    notes.append(note)
                    lanes[chosen_lane].append(note)
                    last_lane = chosen_lane
                    note_id_counter += 1
                    continue

            # Standard Tap / Swipe assignment
            if band == "bass" or centroid < 250:
                primary = 0 if thumb_turn == 0 else 2
                preferred_lanes = [primary, 2 if primary == 0 else 0, 1]
                thumb_turn = 1 - thumb_turn
            elif band == "mid" or (250 <= centroid <= 2800):
                if last_lane == 0:
                    preferred_lanes = [1, 2, 0]
                elif last_lane == 2:
                    preferred_lanes = [1, 0, 2]
                else:
                    preferred_lanes = [1, 0, 2] if thumb_turn == 0 else [1, 2, 0]
            else:
                preferred_lanes = [2, 0, 1]

            if is_hold_active and active_hold_lane in preferred_lanes:
                preferred_lanes = [l for l in preferred_lanes if l != active_hold_lane]

            chosen_lane = None
            for cand_lane in preferred_lanes:
                if t >= lane_busy_until[cand_lane] + min_lane_gap_ms:
                    chosen_lane = cand_lane
                    break

            if chosen_lane is None:
                avail_lanes = [l for l in range(settings.NUM_LANES) if not (is_hold_active and l == active_hold_lane)]
                if not avail_lanes:
                    continue
                earliest_lane = min(avail_lanes, key=lambda l: lane_busy_until[l])
                if t >= lane_busy_until[earliest_lane] + min_global_gap_ms:
                    chosen_lane = earliest_lane
                else:
                    continue

            # Rare Directional Swipe Notes (Left ⬅, Right ➡, Up ⬆)
            can_swipe = allow_swipes and (t - last_swipe_t > 2000) and not is_hold_active
            is_swipe = can_swipe and (random.random() < swipe_chance or (energy > 0.85 and random.random() < 0.15))
            
            if is_swipe:
                note_type: NoteType = "swipe"
                last_swipe_t = t
                if chosen_lane == 0:
                    direction: SwipeDirection = "left" if random.random() > 0.4 else "up"
                elif chosen_lane == 2:
                    direction: SwipeDirection = "right" if random.random() > 0.4 else "up"
                else:
                    direction: SwipeDirection = "up" if random.random() > 0.3 else ("left" if random.random() > 0.5 else "right")

                lane_busy_until[chosen_lane] = t + min_lane_gap_ms
            else:
                note_type: NoteType = "tap"
                direction = None
                lane_busy_until[chosen_lane] = t + min_lane_gap_ms
                if is_hold_active:
                    last_tap_during_hold_t = t

            note = BeatstarNote(
                id=note_id_counter,
                lane=chosen_lane,
                type=note_type,
                timestamp_ms=t,
                duration_ms=None,
                end_timestamp_ms=None,
                direction=direction,
                frequency_band=band,
                energy=round(energy, 3)
            )

            notes.append(note)
            lanes[chosen_lane].append(note)
            last_lane = chosen_lane
            note_id_counter += 1

        tap_count = sum(1 for n in notes if n.type == "tap")
        hold_count = sum(1 for n in notes if n.type == "hold")
        swipe_count = sum(1 for n in notes if n.type == "swipe")
        total_notes = len(notes)

        density = round(total_notes / song_duration, 2) if song_duration > 0 else 0.0

        beatmap_meta = BeatmapMetadata(
            video_id=metadata.get("video_id", "unknown"),
            title=metadata.get("title", "Unknown Track"),
            uploader=metadata.get("uploader"),
            duration_seconds=round(song_duration, 2),
            bpm=bpm,
            total_notes=total_notes,
            tap_count=tap_count,
            hold_count=hold_count,
            swipe_count=swipe_count,
            difficulty=difficulty,
            scroll_duration_ms=scroll_duration_ms,
            density_notes_per_second=density
        )

        return BeatmapResponse(
            video_id=metadata.get("video_id", "unknown"),
            metadata=beatmap_meta,
            notes=notes,
            lanes=lanes
        )
