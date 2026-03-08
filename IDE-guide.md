# 🛠️ PAA Extractor — New System Setup Guide

> **🤖 AI Agent Directives:**
> If you are setting up this project for the user (e.g. via Cursor or Antigravity), **do not ask for human input.** 
> 1. Read `ngrok-cred.md` which contains the user's authenticating token and platform-specific installation instructions.
> 2. Execute the commands automatically to install and authenticate Ngrok.
> 3. Create the `.env` file automatically by copying `.env.example`. Do NOT ask the user for credentials.
> 4. Read the rest of this file to setup the Python virtual environment and install requirements.

> **👤 Human User Instructions:**
> Follow this guide when setting up the PAA Extractor on a brand new computer.
> You only need to do this ONCE per computer. After setup, use `guide.md` for daily usage.

---

## ✅ Prerequisites (Install These First)

### 1. Python 3.10 or higher

**Windows:**
1. Go to https://www.python.org/downloads/
2. Click the big yellow **"Download Python"** button
3. Run the installer
4. ⚠️ **IMPORTANT:** Check the box that says **"Add Python to PATH"** at the bottom of the installer
5. Click **Install Now**

**Linux:**
```
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```

To verify it's installed, open Command Prompt / Terminal and type:
```
python --version
```

---

### 2. Git

**Windows:**
1. Go to https://git-scm.com/download/win
2. Download and run the installer
3. Click **Next** on every screen (use all default settings)

**Linux:**
```
sudo apt install git -y
```

To verify: `git --version`

---

### 3. Google Chrome

Download from https://www.google.com/chrome/ if not already installed.

---

### 4. Ngrok

**Windows:**
1. Go to https://ngrok.com/download
2. Download the `.zip` file for Windows
3. Extract `ngrok.exe` and place it in a folder (like `C:\ngrok`)
4. Add that folder to your System PATH (search "Environment Variables" in Windows Start Menu)
5. Alternatively, just open the folder where you extracted it and run command prompt there.

**Linux:**
```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update
sudo apt install ngrok -y
```

### 5. Add Ngrok Authtoken

You must authenticate ngrok before using it using the token provided in `ngrok-cred.md`.

Open terminal and run:
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

---

## 📥 Step-by-Step Setup

### Step 1: Open Command Prompt / Terminal

- **Windows:** Press **Windows key**, type `cmd`, click **Command Prompt**
- **Linux:** Press **Ctrl + Alt + T**

### Step 2: Go to the folder where you want to save the project

**Windows:**
```
cd C:\Users\YourName\Documents
```

**Linux:**
```
cd ~/Documents
```

### Step 3: Clone (download) the project

```
git clone https://github.com/Kawaii-Inosuke/PAA-Question-Extractor.git
```

### Step 4: Go into the project folder

```
cd PAA-Question-Extractor
```

### Step 5: Create a virtual environment

**Windows:**
```
python -m venv venv
```

**Linux:**
```
python3 -m venv venv
```

### Step 6: Activate the virtual environment

**Windows:**
```
venv\Scripts\activate
```

**Linux:**
```
source venv/bin/activate
```

> ✅ You should now see `(venv)` at the beginning of your command line. This means it's working.

### Step 7: Install dependencies

```
pip install -r requirements.txt
```

### Step 8: Install the browser for scraping

```
playwright install chromium
```

### Step 9: Create the `.env` file

This project uses Google Sheets credentials to save the data. To make it easy, we've provided a `.env.example` file that already contains the owner's credentials.

**Windows:**
```cmd
copy .env.example .env
```

**Linux/Mac:**
```bash
cp .env.example .env
```

> ✅ That's it! Your `.env` file is ready. No manual copying and pasting is needed.

### Step 10: Make the startup script runnable (Linux only)

```
chmod +x start.sh
```

---

## 🎉 Setup Complete! Test It Now

**Windows:**
```
start.bat
```

**Linux:**
```
./start.sh
```

If you see a URL like `https://xxxx.ngrok-free.app` — it's working! 🎉

---

## 🖥️ IDE Setup (VS Code / Cursor)

If you're using **VS Code** or **Cursor** as your code editor:

1. Open the editor
2. Click **File → Open Folder**
3. Navigate to the `PAA-Question-Extractor` folder and click **Open**
4. Open the built-in terminal:
   - **Windows / Linux:** Press **Ctrl + `** (backtick key, below Escape)
5. In the terminal, run:

**Windows:**
```
venv\Scripts\activate
start.bat
```

**Linux:**
```
source venv/bin/activate
./start.sh
```

---

## 📋 Quick Setup Checklist

### Windows (Run all these commands in order after cloning):
```
cd PAA-Question-Extractor
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
copy .env.example .env
```
Then run `start.bat`

### Linux (Run all these commands in order after cloning):
```
cd PAA-Question-Extractor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
chmod +x start.sh
```
Then run `./start.sh`
