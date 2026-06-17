from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import contextlib
import asyncio
import os

from app.core.database import engine, Base
from app.api.routes import router
from app.services.batch_worker import batch_processor

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    flush_task = asyncio.create_task(batch_processor.start_periodic_flush())
    trending_task = asyncio.create_task(batch_processor.start_trending_updater())
    
    yield
    
    flush_task.cancel()
    trending_task.cancel()
    await batch_processor.flush_to_db()

app = FastAPI(title="Typeahead API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Mount Frontend Static Files for Hugging Face Deployment
frontend_dist = os.path.join(os.path.dirname(__file__), "../../Frontend/dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{catchall:path}")
    async def serve_react_app(catchall: str):
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "API running. Frontend build not found."}