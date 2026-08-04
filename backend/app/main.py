from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.analyses.router import router as analyses_router
from app.ai.router import router as ai_router
from app.ai.service import ai_service
from app.embeddings.similarity import similarity_engine
from app.interviews.router import router as interviews_router
from app.jobs.router import router as jobs_router
from app.resumes.router import router as resumes_router
from app.users.router import router as users_router
from app.chat.router import router as chat_router
from app.chat.ai_client import close_chat_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan.

    Loads shared resources during startup and
    releases them gracefully during shutdown.
    """

    # =====================================================
    # Startup
    # =====================================================

    similarity_engine.load()

    yield

    # =====================================================
    # Shutdown
    # =====================================================

    similarity_engine.unload()

    await ai_service.close()

    await close_chat_client()


app = FastAPI(
    title="CareerPilotAI Backend",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

# =====================================================
# REGISTER ROUTERS
# =====================================================

app.include_router(users_router)
app.include_router(resumes_router)
app.include_router(ai_router)
app.include_router(analyses_router)
app.include_router(jobs_router)
app.include_router(chat_router)
app.include_router(interviews_router)


@app.get("/")
def read_root() -> dict[str, str]:
    """
    Health check endpoint.
    """

    return {
        "message": "CareerPilotAI Backend Running Successfully"
    }