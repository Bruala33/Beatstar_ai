from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

NoteType = Literal["tap", "hold", "swipe"]
SwipeDirection = Literal["up", "down", "left", "right"]
DifficultyLevel = Literal["easy", "normal", "hard", "expert", "insane"]

class BeatstarNote(BaseModel):
    id: int = Field(..., description="Unique sequential note identifier")
    lane: int = Field(..., ge=0, le=2, description="Target lane index (0: Left, 1: Center, 2: Right)")
    type: NoteType = Field(..., description="Beatstar note type: 'tap', 'hold', or 'swipe'")
    timestamp_ms: int = Field(..., ge=0, description="Trigger time in milliseconds")
    duration_ms: Optional[int] = Field(None, ge=0, description="Duration in ms for hold notes")
    end_timestamp_ms: Optional[int] = Field(None, ge=0, description="Release time in ms for hold notes")
    direction: Optional[SwipeDirection] = Field(None, description="Swipe direction ('up', 'down', 'left', 'right')")

class BeatmapDifficultyChip(BaseModel):
    id: str
    name: str
    stars: float
    keys: int = 4
    label: str

class CommunityBeatmapItem(BaseModel):
    id: str
    source: str
    source_name: str
    source_badge: str
    source_color: str
    title: str
    artist: str
    creator: str
    thumbnail: str
    download_url: str
    direct_download_url: str
    fallback_download_url: Optional[str] = None
    bpm: float = 120.0
    difficulties: List[BeatmapDifficultyChip]

class BeatmapMetadata(BaseModel):
    id: str
    title: str
    artist: Optional[str] = None
    creator: Optional[str] = None
    difficulty_name: str
    stars: float = 1.0
    duration_seconds: float = 0.0
    bpm: float = 120.0
    total_notes: int = 0
    tap_count: int = 0
    hold_count: int = 0
    swipe_count: int = 0
    num_lanes: int = 3
    scroll_duration_ms: int = 1400
    source: str = "osu"

class BeatmapResponse(BaseModel):
    id: str
    metadata: BeatmapMetadata
    notes: List[BeatstarNote]
    audio_blob_url: Optional[str] = None
