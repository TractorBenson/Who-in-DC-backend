from time import perf_counter

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from routers.dc import router as dc_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://widc.20age1million.com",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start_time = perf_counter()
    status_code = "ERROR"
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed_ms = (perf_counter() - start_time) * 1000
        print(
            f"[API-TIME] {request.method} {request.url.path} "
            f"status={status_code} time={elapsed_ms:.2f}ms"
        )



app.include_router(dc_router)
