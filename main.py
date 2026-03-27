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


class PAARequest(BaseModel):
    keywords: str
    region: str = "us"

    @field_validator("keywords")
    @classmethod
    def keywords_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Keywords cannot be empty")
        return v.strip()

    @field_validator("region")
    @classmethod
    def region_valid(cls, v):
        v = v.lower().strip()
        if v == "in":
            v = "india"
        elif v == "usa":
            v = "us"
            
        if v not in ("us", "india"):
            raise ValueError("Region must be 'us', 'usa', 'india', or 'in'")
        return v


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/paa")
async def extract_paa(request: PAARequest):
    """
    Extract PAA questions for one or more keywords.
    Reuses browser session for batches and targets 16 questions each.
    """
    keyword_list = [k.strip() for k in request.keywords.split(",") if k.strip()]

    if not keyword_list:
        raise HTTPException(status_code=400, detail="No valid keywords provided")

    logger.info(f"Received request: {len(keyword_list)} keywords, region={request.region}")
    logger.info("Target: 16 questions per keyword (Session-only tracking).")

    try:
        # Define callback for incremental saving to Google Sheets
        def incremental_save(result):
            if result.get("questions"):
                # We save one result at a time incrementally
                save_to_sheets([result])
                logger.info(f"Incrementally saved '{result['keyword']}' to Google Sheets.")

        # Scrape with callback, targeting 16 (handled inside scraper.py)
        results = await scrape_multiple_with_callback(keyword_list, request.region, incremental_save)
        
        return {
            "results": results,
            "processed_count": len(results),
            "target": 16
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
