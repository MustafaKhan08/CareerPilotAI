"""CareerPilotAI FastAPI application entry point."""

from fastapi import FastAPI

from app.resumes.router import router as resumes_router
from app.users.router import router as users_router

app = FastAPI(
    title="CareerPilotAI Backend",
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

app.include_router(users_router)
app.include_router(resumes_router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Health check endpoint."""

    return {
        "message": "CareerPilotAI Backend Running Successfully"
    }