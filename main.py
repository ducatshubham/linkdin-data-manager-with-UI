from fastapi import FastAPI
from routes import router
from db import create_indexes
import asyncio

app = FastAPI(title="LinkedIn Data Manager", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    await create_indexes()

app.include_router(router, prefix="/api", tags=["profiles"])

@app.get("/")
async def root():
    return {"message": "LinkedIn Data Manager API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
