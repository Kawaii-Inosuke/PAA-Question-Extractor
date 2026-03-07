# PAA Extractor

Extract **People Also Ask** questions from Google search results. Supports multiple keywords, US and India regions, and returns clean JSON — perfect for SEO research and n8n automation.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browser
playwright install chromium

# 3. Run the server
uvicorn main:app --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## API Usage

### `POST /api/paa`

```bash
curl -X POST http://localhost:8000/api/paa \
  -H "Content-Type: application/json" \
  -d '{"keywords": "seo tips, content marketing", "region": "us"}'
```

**Request body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keywords` | string | Yes | Comma-separated keywords |
| `region` | string | No | `us` (default) or `india` |

**Response:**
```json
{
  "results": [
    {
      "keyword": "seo tips",
      "region": "us",
      "questions": [
        "What are the best SEO tips for beginners?",
        "How can I improve my website SEO?"
      ],
      "count": 12
    }
  ]
}
```

### `GET /health`

Returns `{"status": "ok"}` — useful for monitoring.

## n8n Integration

1. Add an **HTTP Request** node
2. Set **Method** to `POST`
3. Set **URL** to `https://your-domain.com/api/paa`
4. Set **Body Content Type** to `JSON`
5. Set **Body** to:
```json
{
  "keywords": "{{ $json.keywords }}",
  "region": "us"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HEADLESS` | `true` | Set to `false` for local debugging |
| `GOOGLE_SHEET_ID` | | The ID of your Google Sheet from its URL |
| `GOOGLE_PROJECT_ID` | | Your Google Cloud project ID |
| `GOOGLE_CLIENT_EMAIL` | | Service account email address |
| `GOOGLE_PRIVATE_KEY` | | Service account private key string |
| `PROXY_URL` | | Optional: Proxy gateway URL (e.g., http://user:pass@host:port) |

To configure Google Sheets automatically saving:
1. Create a `.env` file in the root directory.
2. Add the `GOOGLE_*` variables from above directly into the file.
3. Share your target Google Sheet with the `GOOGLE_CLIENT_EMAIL` as an Editor.

## Deploy

### Railway
1. Push this folder to a GitHub repo
2. Go to [railway.app](https://railway.app), connect the repo
3. Railway auto-detects the Dockerfile and deploys

### Render
1. Push to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect repo, select Docker environment
4. Deploy

### Docker (manual)
```bash
docker build -t paa-extractor .
docker run -p 8000:8000 paa-extractor
```
