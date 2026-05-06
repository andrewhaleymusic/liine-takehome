FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md assignment.md prompt.md /app/
COPY app /app/app
COPY tests /app/tests
COPY restaurants.csv /app/restaurants.csv

RUN uv pip install --system -e .[dev]

VOLUME ["/data"]
EXPOSE 8000

ENTRYPOINT ["liine"]
