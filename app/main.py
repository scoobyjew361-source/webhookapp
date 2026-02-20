from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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
    return HTMLResponse("lava-verify=a1a1ca323dfe8e77")