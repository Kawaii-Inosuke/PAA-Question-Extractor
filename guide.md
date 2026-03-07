# PAA Extractor — Quick Start Guide

## How It Works

Your PAA Extractor runs **on your laptop** and uses a **Cloudflare Tunnel** to create a public URL.
When n8n sends a request to the public URL → Cloudflare routes it to your laptop → your laptop scrapes Google using your home WiFi (residential IP) → results are saved to Google Sheets.

---

## One-Time Setup (Already Done)

These steps have already been completed:
- ✅ `cloudflared` installed
- ✅ Python virtual environment created
- ✅ All dependencies installed
- ✅ Google Sheets integration configured

---

## Starting the Server (Every Time)

### Option 1: One-Click Start (Recommended)

Open a terminal and run:

```bash
cd "/home/yashodhan/Documents/91NInjas/March 2026/paa draft 2"
./start.sh
```

This will:
1. Start the PAA server on `http://localhost:8000`
2. Create a Cloudflare Tunnel with a public URL (e.g., `https://random-name.trycloudflare.com`)

**Copy the public URL** shown in the terminal and use it in your n8n HTTP Request node.

> **Note:** The public URL changes every time you restart. Update your n8n node with the new URL each time.

### Option 2: Manual Start (If Option 1 Doesn't Work)

**Terminal 1 — Start the server:**
```bash
cd "/home/yashodhan/Documents/91NInjas/March 2026/paa draft 2"
source venv/bin/activate
HEADLESS=false uvicorn main:app --port 8000
```

**Terminal 2 — Start the tunnel:**
```bash
cloudflared tunnel --url http://localhost:8000
```

### Option 3: Backup Tunnel (If Cloudflare Is Blocked)

If `cloudflared` doesn't work on your network, use this SSH-based tunnel instead:

**Terminal 2 — SSH tunnel:**
```bash
ssh -R 80:localhost:8000 nokey@localhost.run
```

This will also give you a public URL.

---

## Stopping the Server

Press **Ctrl+C** in the terminal where `start.sh` is running. This stops both the server and tunnel.

---

## Using with n8n

1. Start the server using one of the options above
2. Copy the **public URL** from the terminal output
3. In your n8n workflow, set the **HTTP Request** node:
   - **Method:** `POST`
   - **URL:** `https://your-tunnel-url.trycloudflare.com/api/paa`
   - **Body Content Type:** `JSON`
   - **Body:**
     ```json
     {
       "keywords": "your keyword here",
       "region": "us"
     }
     ```
4. Run the workflow — questions will be scraped and saved to Google Sheets automatically!

---

## Using the Web Interface Directly

After starting the server, open your browser and go to:
- **Local:** [http://localhost:8000](http://localhost:8000)
- **Public:** `https://your-tunnel-url.trycloudflare.com`

Type your keywords, select the region, and click **Extract Questions**.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Address already in use" | Run `pkill -f "uvicorn main:app"` then try again |
| Cloudflare tunnel won't connect | Use Option 3 (SSH tunnel) instead |
| "Could not find Google search box" | Google showed a CAPTCHA. Try again in a minute |
| Browser doesn't open during scrape | Set `HEADLESS=true` in the start command if you don't want to see the browser |
