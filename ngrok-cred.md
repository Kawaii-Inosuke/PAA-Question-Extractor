# 🔑 Ngrok Credentials and AI Setup Guide

> **🤖 AI Agent Instructions:**
> If you are an AI assistant setting this project up for the user, your goal is to install Ngrok and authenticate it using the token below. 

## The Authtoken
**Token:** `YOUR_NGROK_TOKEN_HERE`

---

## AI Setup Steps 

### 1. Install Ngrok

**If the user is on Windows:**
Run this PowerShell command to install Ngrok via Chocolatey (or use winget):
```powershell
winget install ngrok
```
*(If winget fails, you may need to download the .zip from `https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip`, extract it, and add it to the user's PATH).*

**If the user is on Linux (Debian/Ubuntu):**
```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update
sudo apt install ngrok -y
```

### 2. Authenticate Ngrok
Once `ngrok` is recognized in the terminal, run the following command to link the computer to the account:

```bash
ngrok config add-authtoken YOUR_NGROK_TOKEN_HERE
```

### 3. Next Steps
Once Ngrok is authenticated, you can proceed to the main setup in `IDE-guide.md` or start the server via `start.bat` (Windows) or `start.sh` (Linux).
