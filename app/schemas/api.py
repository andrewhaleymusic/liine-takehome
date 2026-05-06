from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class OpenRestaurantsResponse(BaseModel):
    requested_datetime: str
    restaurants: list[str]
