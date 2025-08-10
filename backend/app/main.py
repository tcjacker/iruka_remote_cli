from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import api, websocket

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")
app.include_router(websocket.router)

@app.get("/")
async def root():
    return {"message": "Gemini Docker Manager Backend is running"}
