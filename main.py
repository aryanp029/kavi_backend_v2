from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from core.config_loader import settings

from routes.oauth import router as oauth_router
from routes.user import router as user_router
from routes.resume import router as resume_router
from routes.onboarding import router as onboarding_router

openapi_tags = [
    {
        "name": "Users",
        "description": "User operations",
    },
    {
        "name": "OAuth",
        "description": "OAuth authentication operations",
    },
    {
        "name": "Health Checks",
        "description": "Application health checks",
    }
]

app = FastAPI(openapi_tags=openapi_tags)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(oauth_router, prefix='/api')
app.include_router(user_router, prefix='/api')
app.include_router(resume_router, prefix='/api')
app.include_router(onboarding_router, prefix='/api')

@app.get("/health", tags=['Health Checks'])
def read_root():
    return {"health": "true"}

