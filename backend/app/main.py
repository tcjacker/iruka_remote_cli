from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth_router, api_router
from . import websocket

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Unprotected auth routes
app.include_router(auth_router, prefix="/api") 
# All other API routes are protected
app.include_router(api_router, prefix="/api") 
# WebSocket router
app.include_router(websocket.router)

@app.get("/")
async def root():
    return {"message": "Gemini Docker Manager Backend is running"}
