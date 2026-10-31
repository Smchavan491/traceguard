import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as connection:
            connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
    except psycopg.Error:
        logger.exception("Could not enable the pgvector extension during startup")
    yield


app = FastAPI(title="TraceGuard", lifespan=lifespan)


@app.get("/health")
def health() -> JSONResponse:
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as connection:
            connection.execute("SELECT 1")
    except psycopg.Error:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "db": "unreachable"},
        )
    return JSONResponse(content={"status": "ok", "db": "ok"})
