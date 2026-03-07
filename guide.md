# 🔍 PAA Extractor — User Guide

> **This guide is for non-developers.** Follow each step exactly as written. Just copy-paste the commands!

---

## 🟢 How to Start the PAA Extractor (Do This Every Time)

### Step 1: Open the Terminal

- On your keyboard, press **Ctrl + Alt + T** — this opens the Terminal (a black window where you type commands)

### Step 2: Start the server

Copy this entire line below and **paste it into the Terminal** (use Ctrl+Shift+V to paste in Terminal), then press **Enter**:

```
cd "/home/yashodhan/Documents/91NInjas/March 2026/paa draft 2" && ./start.sh
```

### Step 3: Wait for the URL

After about 10 seconds, you will see something like this in the Terminal:

```
  ┌─────────────────────────────────────────────────────┐
  │  COPY THIS URL FOR n8n:                             │
  │                                                     │
  │  https://some-random-words.trycloudflare.com/api/paa│
  │                                                     │
  └─────────────────────────────────────────────────────┘
```

### Step 4: Copy the URL

- **Select the URL** (the `https://...trycloudflare.com/api/paa` part) with your mouse
- Press **Ctrl+Shift+C** to copy it

### Step 5: Paste it in n8n

- Open your **n8n workflow**
- Open the **HTTP Request** node
- Paste the URL into the **URL field**
- The body should be:
```json
{
  "keywords": "your keyword here",
  "region": "us"
}
```
- Click **Execute** to test it!

---

## 🔴 How to Stop the Server

- Go back to the Terminal where the server is running
- Press **Ctrl + C** on your keyboard
- The server will shut down

---

## 🌐 How to Use the Web Interface (Instead of n8n)

While the server is running, you can also use it from your browser:

1. Open **Google Chrome** (or any browser)
2. In the address bar, type: `http://localhost:8000`
3. Press **Enter**
4. You will see the PAA Extractor page
5. Type your keywords, select the region, and click **Extract Questions**

---

## ❓ Common Problems and Solutions

### "Address already in use" error

This means the server is already running. Fix it by running this command first:

```
pkill -f "uvicorn main:app"
```

Then run the start command again from Step 2.

### "Tunnel took too long" or no URL appears

Your WiFi might be blocking the tunnel. Try these fixes:
1. **Switch to a different WiFi** (like your phone hotspot) and try again
2. If that doesn't work, you can still use the tool **locally** by opening `http://localhost:8000` in your browser — it works without the tunnel!

### Browser opens during scraping

This is normal! The scraper opens a hidden browser to visit Google. It will close automatically after extracting the questions.

### No questions found

Sometimes Google doesn't show PAA questions for certain keywords. The scraper will automatically retry up to 3 times. If it still shows 0, try a different keyword.

---

## 📋 Quick Reference

| What you want to do | What to do |
|---------------------|------------|
| **Start the server** | Open Terminal → paste: `cd "/home/yashodhan/Documents/91NInjas/March 2026/paa draft 2" && ./start.sh` |
| **Stop the server** | Press `Ctrl + C` in the Terminal |
| **Use in browser** | Go to `http://localhost:8000` |
| **Fix "address in use"** | Run: `pkill -f "uvicorn main:app"` then start again |
