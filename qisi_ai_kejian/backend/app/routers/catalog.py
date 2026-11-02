from fastapi import APIRouter

from ..schemas import ModelInfo, StyleInfo
from ..services import mock_ai

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("/styles", response_model=list[StyleInfo])
def styles() -> list[StyleInfo]:
    return [StyleInfo(**s) for s in mock_ai.list_styles()]


@router.get("/models", response_model=list[ModelInfo])
def models() -> list[ModelInfo]:
    return [ModelInfo(**m) for m in mock_ai.list_models()]
