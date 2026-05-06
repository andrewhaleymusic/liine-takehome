from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.api import HealthResponse, OpenRestaurantsResponse
from app.services.availability import find_open_restaurants

router = APIRouter()

LOCAL_DATETIME_PATTERN = r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?$"
LOCAL_DATETIME_EXAMPLE = "2026-05-06T11:00:00"
DATETIME_ADAPTER = TypeAdapter(datetime)
LOCAL_DATETIME_REGEX = re.compile(LOCAL_DATETIME_PATTERN)
RequestedDateTimeParam = Annotated[
    str,
    Query(
        alias="datetime",
        description="Naive local datetime in ISO-like form, for example 2026-05-06T11:00:00.",
        examples=[LOCAL_DATETIME_EXAMPLE],
    ),
]


def parse_requested_datetime(requested_datetime: str) -> datetime:
    if not LOCAL_DATETIME_REGEX.fullmatch(requested_datetime):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid datetime. Use a naive local datetime like {LOCAL_DATETIME_EXAMPLE}.",
        )

    try:
        parsed_datetime = DATETIME_ADAPTER.validate_python(requested_datetime)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid datetime. Use a naive local datetime like {LOCAL_DATETIME_EXAMPLE}.",
        ) from exc

    if parsed_datetime.tzinfo is not None and parsed_datetime.utcoffset() is not None:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid datetime. Use a naive local datetime like {LOCAL_DATETIME_EXAMPLE}.",
        )

    return parsed_datetime


@router.get("/health", response_model=HealthResponse, tags=["health"])
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/restaurants/open", response_model=OpenRestaurantsResponse, tags=["restaurants"])
def list_open_restaurants(
    requested_datetime: RequestedDateTimeParam,
    db: Session = Depends(get_db),
) -> OpenRestaurantsResponse:
    parsed_datetime = parse_requested_datetime(requested_datetime)
    restaurants = find_open_restaurants(db, parsed_datetime)
    return OpenRestaurantsResponse(
        requested_datetime=requested_datetime,
        restaurants=restaurants,
    )
