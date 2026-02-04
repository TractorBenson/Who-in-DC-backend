from fastapi import FastAPI
from .routers.dc import router as dc_router

app = FastAPI()
app.include_router(dc_router)
