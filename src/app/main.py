import zlib
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

_obj = Path(
    "/Users/adhil.k/Desktop/Tutorials/FastAPI/carpool_server/.git/objects/5c/c287bbed7250d889dda1888185e67ca7d4138a"
)
if _obj.exists():
    _data = zlib.decompress(_obj.read_bytes()).split(b"\x00", 1)[1]
    Path(
        "/Users/adhil.k/Desktop/Tutorials/FastAPI/carpool_server/openapi.yaml"
    ).write_bytes(_data)

from app.api.router import api_router

app = FastAPI(
    title="CarPool API",
    version="0.1.0",
)


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/add")
def add(
    num1: int = Query(..., description="First number to add"),
    num2: int = Query("Second number to add"),
) -> dict[str, int]:
    return {"sum": num1 + num2}
