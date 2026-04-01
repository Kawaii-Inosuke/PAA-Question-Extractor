"""
PAA Extractor — FastAPI Server
Serves the frontend and provides the /api/paa endpoint for n8n integration.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
import logging

from scraper import scrape_multiple_with_callback
from google_sheets import save_to_sheets, get_existing_counts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("paa_api")

app = FastAPI(
    title="PAA Extractor",
    description="Extract People Also Ask questions from Google",
    version="1.0.0",
)

# CORS — allow all origins for n8n compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class KeywordItem(BaseModel):
    keyword: str
    region: str = "us"
    kw_type: str = "Primary"

    @field_validator("region")
    @classmethod
    def region_valid(cls, v):
        v = v.lower().strip()
        if v in ("usa", "us"):
            return "us"
        if v in ("in", "india"):
            return "in"
        raise ValueError("Region must be 'us' or 'in'")

    @field_validator("kw_type")
    @classmethod
    def kw_type_valid(cls, v):
        v = v.strip().capitalize()
        if v not in ("Primary", "Secondary"):
            raise ValueError("kw_type must be 'Primary' or 'Secondary'")
        return v

    @property
    def target(self) -> int:
        return 8 if self.kw_type == "Primary" else 4


class PAARequest(BaseModel):
    keywords: str | list[KeywordItem]
    region: str = "us"
    kw_type: str = "Primary"

    @field_validator("region")
    @classmethod
    def region_valid(cls, v):
        v = v.lower().strip()
        if v in ("usa", "us"):
            return "us"
        if v in ("in", "india"):
            return "in"
        raise ValueError("Region must be 'us' or 'in'")

    @field_validator("kw_type")
    @classmethod
    def kw_type_valid(cls, v):
        v = v.strip().capitalize()
        if v not in ("Primary", "Secondary"):
            raise ValueError("kw_type must be 'Primary' or 'Secondary'")
        return v


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/paa")
async def extract_paa(request: PAARequest):
    """
    Extract PAA questions for one or more keywords.
    Reuses browser session for batches.
    Primary keywords → 8 questions, Secondary → 4 questions.
    """
    # Build keyword list and per-keyword targets
    if isinstance(request.keywords, list):
        # Structured input: list of KeywordItem objects
        items = request.keywords
        keyword_list = [item.keyword.strip() for item in items if item.keyword.strip()]
        targets = {item.keyword.strip(): item.target for item in items if item.keyword.strip()}
        region = items[0].region if items else request.region
    else:
        # Simple string input: apply top-level region and kw_type to all
        keyword_list = [k.strip() for k in request.keywords.split(",") if k.strip()]
        target = 8 if request.kw_type == "Primary" else 4
        targets = {k: target for k in keyword_list}
        region = request.region

    if not keyword_list:
        raise HTTPException(status_code=400, detail="No valid keywords provided")

    logger.info(f"Received request: {len(keyword_list)} keywords, region={region}")
    logger.info(f"Targets: {targets}")

    try:
        # Define callback for incremental saving to Google Sheets
        def incremental_save(result):
            if result.get("questions"):
                save_to_sheets([result])
                logger.info(f"Incrementally saved '{result['keyword']}' to Google Sheets.")

        results = await scrape_multiple_with_callback(keyword_list, region, incremental_save, targets=targets)

        return {
            "results": results,
            "processed_count": len(results),
            "targets": targets
        }
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML page."""
    return FileResponse("static/index.html")
