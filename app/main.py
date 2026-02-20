from fastapi import FastAPI
from pathlib import Path
from fastapi.responses import FileResponse
from app.api.routers import router as api_router
from app.site_pages import router as site_router

app = FastAPI()
app.include_router(api_router)
app.include_router(site_router)

@app.get("/health")
def health():
    return {"status": "ok"}

 
@app.get("/lava-verify_a1a1ca323dfe8e77.html", include_in_schema=False)
async def lava_verify_file():
    file_path = Path(__file__).resolve().parent / "verify" / "lava-verify_a1a1ca323dfe8e77.html"
    return FileResponse(file_path)