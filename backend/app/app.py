from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn  
from routes.webhook_listener import router as webhook_listener
from routes.jobs import router as jobs_router
from routes.notifications import router as notifications_router

app = FastAPI(title="HealPipe API", version="1.0.0")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setting up the Routes 
app.include_router(webhook_listener)
app.include_router(jobs_router)
app.include_router(notifications_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
