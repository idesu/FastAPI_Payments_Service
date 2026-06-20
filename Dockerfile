FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.4.1

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . .

RUN chmod +x entrypoint.sh

ENV PYTHONPATH=/app

ENTRYPOINT ["./entrypoint.sh"]