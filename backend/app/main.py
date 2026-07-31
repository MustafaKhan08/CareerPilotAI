from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.analyses.router import router as analyses_router
from app.ai.router import router as ai_router
from app.ai.service import ai_service
from app.resumes.router import router as resumes_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan.

    Ensures shared resources are released gracefully during shutdown.
    """
    yield
    await ai_service.close()


app = FastAPI(
    title="CareerPilotAI Backend",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

app.include_router(users_router)
app.include_router(resumes_router)
app.include_router(ai_router)
app.include_router(analyses_router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Health check endpoint."""

    return {
        "message": "CareerPilotAI Backend Running Successfully"
    }