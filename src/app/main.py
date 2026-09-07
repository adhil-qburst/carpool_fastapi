from fastapi import FastAPI, Query

from app.api.router import api_router

app = FastAPI(
    title="CarPool API",
    version="0.1.0",
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
