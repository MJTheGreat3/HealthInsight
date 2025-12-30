from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bson import ObjectId
from src.db.mongoWrapper import getMongo
from bson.json_util import dumps
from src.routers import report,llmReport,user,dashboard, access,chat
from src.core.config import settings
import json

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

# app = FastAPI()

# CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://frontend:80",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report.router)
app.include_router(llmReport.router)
app.include_router(user.router)
app.include_router(dashboard.router)
app.include_router(access.router)
app.include_router(chat.router)

