from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.init_db import create_tables
from app.db.models import OpeningIntervalModel, Restaurant
from app.db.session import build_engine, get_db
from app.main import app


def seed_restaurant(
    session: Session,
    *,
    name: str,
    intervals: list[tuple[int, int]],
) -> None:
    restaurant = Restaurant(name=name)
    session.add(restaurant)
    session.flush()
    for start_minute, end_minute in intervals:
        session.add(
            OpeningIntervalModel(
                restaurant_id=restaurant.id,
                start_minute=start_minute,
                end_minute=end_minute,
            )
        )
    session.commit()


def create_api_client(tmp_path) -> tuple[TestClient, str]:
    database_url = f"sqlite:///{tmp_path / 'api.db'}"
    engine = build_engine(database_url)
    create_tables(engine)

    def override_get_db():
        session = Session(engine)
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, database_url


def test_open_restaurants_endpoint_returns_matching_names(tmp_path) -> None:
    client, database_url = create_api_client(tmp_path)
    engine = build_engine(database_url)
    with Session(engine) as session:
        seed_restaurant(session, name="Bravo", intervals=[(660, 780)])
        seed_restaurant(session, name="Alpha", intervals=[(660, 780)])

    response = client.get("/restaurants/open", params={"datetime": "2026-05-04T11:30:00"})

    assert response.status_code == 200
    assert response.json() == {
        "requested_datetime": "2026-05-04T11:30:00",
        "restaurants": ["Alpha", "Bravo"],
    }
    app.dependency_overrides.clear()


def test_open_restaurants_endpoint_returns_empty_list_when_none_are_open(tmp_path) -> None:
    client, database_url = create_api_client(tmp_path)
    engine = build_engine(database_url)
    with Session(engine) as session:
        seed_restaurant(session, name="Alpha", intervals=[(660, 780)])

    response = client.get("/restaurants/open", params={"datetime": "2026-05-04T15:00:00"})

    assert response.status_code == 200
    assert response.json() == {
        "requested_datetime": "2026-05-04T15:00:00",
        "restaurants": [],
    }
    app.dependency_overrides.clear()


def test_open_restaurants_endpoint_rejects_invalid_datetime(tmp_path) -> None:
    client, _ = create_api_client(tmp_path)

    response = client.get("/restaurants/open", params={"datetime": "not-a-date"})

    assert response.status_code == 422
    app.dependency_overrides.clear()


def test_open_restaurants_endpoint_rejects_timezone_aware_datetime(tmp_path) -> None:
    client, _ = create_api_client(tmp_path)

    response = client.get("/restaurants/open", params={"datetime": "2026-05-04T11:30:00Z"})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid datetime. Use a naive local datetime like 2026-05-06T11:00:00."
    }
    app.dependency_overrides.clear()


def test_open_restaurants_endpoint_handles_week_wrap_intervals(tmp_path) -> None:
    client, database_url = create_api_client(tmp_path)
    engine = build_engine(database_url)
    with Session(engine) as session:
        seed_restaurant(session, name="Late Spot", intervals=[(0, 120), (9360, 10080)])

    sunday_response = client.get("/restaurants/open", params={"datetime": "2026-05-10T13:00:00"})
    monday_response = client.get("/restaurants/open", params={"datetime": "2026-05-11T01:00:00"})

    assert sunday_response.status_code == 200
    assert sunday_response.json()["restaurants"] == ["Late Spot"]
    assert monday_response.status_code == 200
    assert monday_response.json()["restaurants"] == ["Late Spot"]
    app.dependency_overrides.clear()


def test_open_restaurants_endpoint_returns_empty_list_for_empty_schema(tmp_path) -> None:
    client, _ = create_api_client(tmp_path)

    response = client.get("/restaurants/open", params={"datetime": "2026-05-04T11:30:00"})

    assert response.status_code == 200
    assert response.json() == {
        "requested_datetime": "2026-05-04T11:30:00",
        "restaurants": [],
    }
    app.dependency_overrides.clear()


def test_openapi_describes_local_datetime_as_plain_string(tmp_path) -> None:
    client, _ = create_api_client(tmp_path)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi_schema = response.json()
    query_parameter = next(
        parameter
        for parameter in openapi_schema["paths"]["/restaurants/open"]["get"]["parameters"]
        if parameter["name"] == "datetime"
    )
    assert query_parameter["schema"]["type"] == "string"
    assert "format" not in query_parameter["schema"]

    response_property = openapi_schema["components"]["schemas"]["OpenRestaurantsResponse"][
        "properties"
    ]["requested_datetime"]
    assert response_property["type"] == "string"
    assert "format" not in response_property
    app.dependency_overrides.clear()
