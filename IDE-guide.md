# 🛠️ PAA Extractor — New System Setup Guide

> **Follow this guide when setting up the PAA Extractor on a brand new computer.**
> You only need to do this ONCE per computer. After setup, use `guide.md` for daily usage.

---

## ✅ Prerequisites (Must Be Installed First)

Before you begin, make sure these are installed on your system:

### 1. Python 3.10 or higher

Check if Python is installed:
```
python3 --version
```

If NOT installed, run:
```
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```

### 2. Git

Check if Git is installed:
```
git --version
```

If NOT installed, run:
```
sudo apt install git -y
```

### 3. Google Chrome (for Playwright)

Check if Chrome is installed:
```
google-chrome --version
```

If NOT installed, download it from: https://www.google.com/chrome/

---

## 📥 Step-by-Step Setup

### Step 1: Clone the repository

Open Terminal (**Ctrl + Alt + T**) and run:

```
cd ~/Documents
git clone https://github.com/Kawaii-Inosuke/PAA-Question-Extractor.git
cd PAA-Question-Extractor
```

### Step 2: Create a Python virtual environment

```
python3 -m venv venv
```

### Step 3: Activate the virtual environment

```
source venv/bin/activate
```

> After this, you should see `(venv)` at the beginning of your terminal line

### Step 4: Install Python dependencies

```
pip install -r requirements.txt
```

### Step 5: Install Playwright browser

```
playwright install chromium
```

### Step 6: Install Cloudflare Tunnel

```
curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i /tmp/cloudflared.deb
```

> It will ask for your computer password. Type it and press Enter (the password won't be visible while typing — this is normal).

### Step 7: Create the `.env` file

You need to create a file called `.env` in the project folder with your Google Sheets credentials. Run this command:

```
nano .env
```

Then paste the following content **(replace the placeholder values with your actual credentials)**:

```
GOOGLE_SHEET_ID=your_google_sheet_id_here
GOOGLE_PROJECT_ID=your_google_project_id_here
GOOGLE_CLIENT_EMAIL=your_service_account_email_here
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
```

To save the file: press **Ctrl + O**, then **Enter**, then **Ctrl + X** to exit.

> **Where to get these values:** Ask the project owner for the Google Sheets service account credentials, or check the original `.env` file on the existing setup.

### Step 8: Make the startup script executable

```
chmod +x start.sh
```

### Step 9: Update the path in start.sh and guide.md

The `guide.md` and `start.sh` files contain a hardcoded path. If you cloned the repo to a different location, update the path in `guide.md` to match your new location.

---

## 🎉 Setup Complete!

You can now start the server by running:

```
./start.sh
```

Refer to `guide.md` for daily usage instructions.

---

## 📋 Quick Setup Checklist

Copy-paste ALL these commands in order to set up everything at once (after cloning):

```bash
cd ~/Documents/PAA-Question-Extractor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i /tmp/cloudflared.deb
chmod +x start.sh
```

Then create the `.env` file (Step 7 above) and you're ready to go!

---

## 🖥️ IDE Setup (VS Code / Cursor)

If you're using **VS Code** or **Cursor** as your code editor:

1. Open the editor
2. Click **File → Open Folder**
3. Navigate to the project folder (`PAA-Question-Extractor`) and click **Open**
4. Open the built-in terminal: press **Ctrl + `** (backtick key, below Escape)
5. In the terminal, run:
```
source venv/bin/activate
./start.sh
```

That's it! The server will start right inside your editor.
