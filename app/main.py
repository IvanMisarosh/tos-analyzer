from fastapi import FastAPI
from app.auth.routes import router as auth_router
from app.analyzer.routes import router as analyzer_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(analyzer_router, tags=["analyzer"])
