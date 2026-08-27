from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl

NoteType = Literal["tap", "hold", "swipe"]
SwipeDirection = Literal["up", "down", "left", "right"]
DifficultyLevel = Literal["easy", "normal", "hard", "expert"]

class BeatstarNote(BaseModel):
    id: int = Field(..., description="Unique sequential note identifier")
    lane: int = Field(..., ge=0, le=2, description="Target lane index (0: Left, 1: Center, 2: Right)")
    type: NoteType = Field(..., description="Beatstar note type: 'tap', 'hold', or 'swipe'")
    timestamp_ms: int = Field(..., ge=0, description="Trigger time in milliseconds")
    duration_ms: Optional[int] = Field(None, ge=0, description="Duration in ms for hold notes")
    end_timestamp_ms: Optional[int] = Field(None, ge=0, description="Release time in ms for hold notes")
    direction: Optional[SwipeDirection] = Field(None, description="Swipe direction ('up', 'down', 'left', 'right')")
    frequency_band: Optional[str] = Field(None, description="Acoustic frequency band trigger ('bass', 'mid', 'high')")
    energy: Optional[float] = Field(None, description="Normalized transient energy level [0.0 - 1.0]")

class BeatmapMetadata(BaseModel):
    video_id: str
    title: str
    uploader: Optional[str] = None
    duration_seconds: float
    bpm: float
    total_notes: int
    tap_count: int
    hold_count: int
    swipe_count: int
    difficulty: str
    scroll_duration_ms: int = 1400
    density_notes_per_second: float

class GenerateBeatmapRequest(BaseModel):
    url: str = Field(..., description="Full YouTube URL or YouTube Video ID (e.g. https://www.youtube.com/watch?v=...)")
    difficulty: DifficultyLevel = Field("normal", description="Beatmap difficulty density: 'easy', 'normal', 'hard', 'expert'")
    snap_to_grid: bool = Field(True, description="Whether to snap timestamps to estimated rhythmic musical sub-beats")
    onset_sensitivity: Optional[float] = Field(1.0, ge=0.2, le=3.0, description="Multiplier for transient detection sensitivity")

class BeatmapResponse(BaseModel):
    video_id: str
    metadata: BeatmapMetadata
    notes: List[BeatstarNote]
    lanes: List[List[BeatstarNote]] = Field(..., description="Notes grouped by lane [Lane 0, Lane 1, Lane 2]")
