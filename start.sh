#!/bin/bash
# PAA Extractor — One-click startup script
# This starts the server AND creates a public tunnel URL

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo "  ╔═══════════════════════════════════╗"
echo "  ║   PAA Extractor — Starting Up     ║"
echo "  ╚═══════════════════════════════════╝"
echo ""

# Kill any existing instances first
echo "  [0] Cleaning up old processes..."
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "ngrok" 2>/dev/null
sleep 1

# 1. Activate virtual environment
source venv/bin/activate

# 2. Start the PAA server in the background
echo "  [1/2] Starting PAA server on http://localhost:8000 ..."
HEADLESS=false uvicorn main:app --port 8000 > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2

# Check if server started
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "  ERROR: Server failed to start!"
    echo "  Try: pkill -f 'uvicorn main:app' && ./start.sh"
    exit 1
fi
echo "  ✓ Server running (PID: $SERVER_PID)"
echo ""

# 3. Start ngrok and capture the URL
echo "  [2/2] Creating public tunnel (using ngrok)..."
TUNNEL_LOG="/tmp/ngrok.log"
# Start ngrok in background, logging to file
ngrok http 8000 --log=stdout > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

# Wait and extract the tunnel URL
TUNNEL_URL=""
for i in $(seq 1 15); do
    sleep 1
    # Ngrok logs the URL with "url=https://..."
    TUNNEL_URL=$(grep -oP 'url=https://[a-zA-Z0-9-]+\.ngrok-free\.(app|dev)' "$TUNNEL_LOG" 2>/dev/null | head -1 | cut -d= -f2)
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
done

if [ -z "$TUNNEL_URL" ]; then
    echo "  ⚠ Tunnel took too long to start. Check /tmp/ngrok.log"
    echo "  Your server is still running locally at: http://localhost:8000"
    echo ""
else
    echo ""
    echo "  ╔═══════════════════════════════════════════════════════╗"
    echo "  ║            PAA Extractor is LIVE! ✓                  ║"
    echo "  ╠═══════════════════════════════════════════════════════╣"
    echo "  ║                                                       ║"
    echo "  ║  Local:  http://localhost:8000                        ║"
    echo "  ║                                                       ║"
    echo "  ╚═══════════════════════════════════════════════════════╝"
    echo ""
    echo "  ┌─────────────────────────────────────────────────────┐"
    echo "  │  COPY THIS URL FOR n8n:                             │"
    echo "  │                                                     │"
    echo "  │  ${TUNNEL_URL}/api/paa"
    echo "  │                                                     │"
    echo "  │  NOTE: Ngrok provides a permanent URL!              │"
    echo "  │  You only need to configure this in n8n once.       │"
    echo "  └─────────────────────────────────────────────────────┘"
    echo ""
    echo "  Public URL: $TUNNEL_URL"
    echo ""
fi

echo "  Press Ctrl+C to stop everything."
echo ""

# Handle Ctrl+C to stop both processes
trap "echo ''; echo '  Shutting down...'; kill $SERVER_PID $TUNNEL_PID 2>/dev/null; exit 0" INT TERM

# Wait for either process to exit
wait
