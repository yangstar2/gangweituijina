from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ContentType = Literal["courseware", "exam"]


class SessionCreate(BaseModel):
    content_type: ContentType
    title: str | None = None
    # mock auth: omit to use default mock openid
    openid: str | None = None


class SessionOut(BaseModel):
    id: int
    content_type: ContentType
    title: str | None
    status: str
    created_at: str
    updated_at: str


class ChatMessageIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class TeacherTurnOut(BaseModel):
    role: Literal["teacher"] = "teacher"
    content: str
    clarifying_done: bool = False
    suggested_replies: list[str] = Field(default_factory=list)


class ChatReplyOut(BaseModel):
    user_message_id: int
    teacher: TeacherTurnOut
    session_status: str
    outline: OutlineOut | None = None


class OutlineOut(BaseModel):
    session_id: int
    key_points: list[str]
    outline: list[dict]
    notes: list[str]
    raw_summary: str | None = None


class PreviewPage(BaseModel):
    page_no: int
    title: str
    bullets: list[str]
    speaker_note: str | None = None
    mock_image_hint: str | None = None


class PreviewOut(BaseModel):
    session_id: int
    style_id: str
    model_id: str
    pages: list[PreviewPage]


class StyleInfo(BaseModel):
    id: str
    name: str
    description: str
    palette: list[str]


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: str
    recommended: bool = False
