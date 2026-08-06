from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.admin.scripts_router import router as admin_scripts_router
from backend.admin.users_router import router as admin_users_router
from backend.auth.router import router as auth_router
from backend.core.config import Config
from backend.core.responses import register_exception_handlers
from backend.models.router import router as model_versions_router
from backend.scripts.router import router as scripts_router
from backend.users.router import router as users_router
from backend.simulations.router import router as simulations_router



def create_app():
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(scripts_router)
    app.include_router(admin_users_router)
    app.include_router(admin_scripts_router)
    app.include_router(model_versions_router)
    app.include_router(simulations_router)

    return app


app = create_app()
