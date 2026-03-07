#!/bin/bash
# PAA Extractor — One-click startup script
# This starts the server AND creates a public tunnel URL

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "==============================="
echo "  PAA Extractor — Starting Up"
echo "==============================="
echo ""

# Kill any existing instances first
echo "[0] Cleaning up old processes..."
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 1

# 1. Activate virtual environment
source venv/bin/activate

# 2. Start the PAA server in the background
echo "[1/2] Starting PAA server on http://localhost:8000 ..."
HEADLESS=false uvicorn main:app --port 8000 &
SERVER_PID=$!
sleep 2

# Check if server started
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "ERROR: Server failed to start!"
    exit 1
fi
echo "       Server running (PID: $SERVER_PID)"
echo ""

# 3. Start Cloudflare Tunnel
echo "[2/2] Creating public tunnel with Cloudflare..."
echo "       (Your public URL will appear below)"
echo ""
cloudflared tunnel --url http://localhost:8000 2>&1 &
TUNNEL_PID=$!

# Wait for the tunnel URL to appear
sleep 5

echo ""
echo "==============================="
echo "  PAA Extractor is LIVE!"
echo "==============================="
echo ""
echo "  Local:  http://localhost:8000"
echo "  Public: (see the trycloudflare.com URL above)"
echo ""
echo "  Use the PUBLIC URL in n8n HTTP Request node."
echo "  Press Ctrl+C to stop everything."
echo ""

# Handle Ctrl+C to stop both processes
trap "echo ''; echo 'Shutting down...'; kill $SERVER_PID $TUNNEL_PID 2>/dev/null; exit 0" INT TERM

# Wait for either process to exit
wait
