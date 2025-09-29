from fastapi import FastAPI
from .routes import manuscripts, edits

app = FastAPI(title="BookEditor API")

app.include_router(manuscripts.router, prefix="/manuscripts", tags=["manuscripts"])
app.include_router(edits.router, prefix="/edits", tags=["edits"])

@app.get("/")
async def root():
    return {"status": "ok"}
