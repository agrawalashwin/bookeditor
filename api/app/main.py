from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import manuscripts, edits
from .database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BookEditor API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(manuscripts.router, prefix="/manuscripts", tags=["manuscripts"])
app.include_router(edits.router, prefix="/edits", tags=["edits"])

@app.get("/")
async def root():
    return {"status": "ok", "message": "BookEditor API is running"}
