# 🔍 PAA Extractor — User Guide

> **This guide is for non-developers.** Follow each step exactly as written. Just copy-paste the commands!

---

## 🟢 How to Start the PAA Extractor (Do This Every Time)

### Step 1: Open the Terminal / Command Prompt

- **Windows:** Press the **Windows key**, type `cmd`, and click **Command Prompt**
- **Linux:** Press **Ctrl + Alt + T**

### Step 2: Go to the project folder

Type this command and press **Enter**. Replace the path with wherever you saved the project:

**Windows:**
```
cd C:\Users\YourName\Documents\PAA-Question-Extractor
```

**Linux:**
```
cd ~/Documents/PAA-Question-Extractor
```

> 💡 **Tip:** If you're not sure where the folder is, open it in your File Explorer, click on the address bar at the top, and copy the path from there.

### Step 3: Start the server

**Windows:**
```
start.bat
```

**Linux:**
```
./start.sh
```

### Step 4: Wait for the URL (about 10 seconds)

You will see something like this appear:

```
  ┌─────────────────────────────────────────────────────┐
  │  COPY THIS URL FOR n8n:                             │
  │                                                     │
  │  https://some-random-words.trycloudflare.com/api/paa│
  │                                                     │
  └─────────────────────────────────────────────────────┘
```

### Step 5: Copy the URL

- **Select** the full URL (the `https://...trycloudflare.com/api/paa` part)
- **Copy it:**
  - Windows: **Ctrl + C**
  - Linux Terminal: **Ctrl + Shift + C**

### Step 6: Paste it in n8n

1. Open your **n8n workflow**
2. Open the **HTTP Request** node
3. Paste the URL into the **URL field**
4. Set the method to **POST**
5. Set Body Content Type to **JSON**
6. In the body, type:
```json
{
  "keywords": "your keyword here",
  "region": "us"
}
```
7. Click **Execute** to run!

> ⚠️ **The URL changes every time you restart.** You will need to copy the new URL and update it in n8n each time.

---

## 🔴 How to Stop the Server

- Go back to the Terminal / Command Prompt where the server is running
- Press **Ctrl + C** on your keyboard
- The server will shut down

---

## 🌐 How to Use the Web Interface (Instead of n8n)

While the server is running, you can also use it directly in your browser:

1. Open **Google Chrome** (or any browser)
2. In the address bar, type: `http://localhost:8000`
3. Press **Enter**
4. You will see the PAA Extractor page
5. Type your keywords, select the region, and click **Extract Questions**

---

## ❓ Common Problems and Solutions

| Problem | Solution |
|---------|----------|
| **"Address already in use"** | **Windows:** `taskkill /F /IM "uvicorn.exe"` then start again. **Linux:** `pkill -f "uvicorn main:app"` then start again. |
| **No URL appears after 15 seconds** | Switch to a different WiFi (try phone hotspot) and run start again |
| **"command not found" error** | Make sure you ran the setup from IDE-guide.md first |
| **Browser opens during scraping** | This is normal! The scraper opens a browser to visit Google. It closes automatically |
| **No questions found** | Google didn't show PAA for that keyword. The scraper retries 3 times automatically. Try a different keyword |
