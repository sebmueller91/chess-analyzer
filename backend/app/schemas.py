from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    username: str
    time_control: str = "all"
    game_count: int = 50


class AnalyzeResponse(BaseModel):
    status: str
    username: str


class PlayerResponse(BaseModel):
    username: str
    last_analyzed_at: Optional[datetime] = None
    games_analyzed: int = 0
    time_control: Optional[str] = None
    status: str = "idle"
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class PlayersListResponse(BaseModel):
    players: list[PlayerResponse]


class StatusResponse(BaseModel):
    username: str
    status: str
    progress: dict[str, int] = Field(default_factory=dict)


class OpeningPerformance(BaseModel):
    name: str
    eco: Optional[str] = None
    games_played: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    avg_accuracy: float


class PhaseStats(BaseModel):
    mistakes: int = 0
    inaccuracies: int = 0
    blunders: int = 0
    avg_accuracy: float = 0.0


class ColorStats(BaseModel):
    games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_rate: float = 0.0
    avg_accuracy: float = 0.0
    avg_mistakes: float = 0.0


class WeaknessItem(BaseModel):
    name: str
    description: str
    frequency: int
    severity: str
    phase: str
    examples: list[dict[str, Any]] = Field(default_factory=list)


class MistakeExample(BaseModel):
    game_opponent: str
    game_date: Optional[str] = None
    move_number: int
    phase: str
    played_move: str
    best_move: str
    eval_before: float
    eval_after: float
    fen: str
    classification: str
    opening_name: Optional[str] = None
    player_color: str
    result: str


class TrainingRecommendation(BaseModel):
    title: str
    description: str
    priority: str
    related_weakness: str


class SummaryStats(BaseModel):
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_rate: float = 0.0
    avg_accuracy: float = 0.0


class ReportResponse(BaseModel):
    username: str
    summary: SummaryStats
    top_weaknesses: list[WeaknessItem] = Field(default_factory=list)
    openings: list[OpeningPerformance] = Field(default_factory=list)
    phase_distribution: dict[str, PhaseStats] = Field(default_factory=dict)
    color_comparison: dict[str, ColorStats] = Field(default_factory=dict)
    mistake_examples: list[MistakeExample] = Field(default_factory=list)
    training_recommendations: list[TrainingRecommendation] = Field(default_factory=list)
    coaching_summary: Optional[str] = None


class ChatRequest(BaseModel):
    username: str
    message: str


class ChatResponse(BaseModel):
    response: str


class ErrorResponse(BaseModel):
    detail: str
