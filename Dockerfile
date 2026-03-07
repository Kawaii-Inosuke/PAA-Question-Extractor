# Use the official Microsoft Playwright image which includes all dependencies
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium (dependencies are already in the base image)
RUN playwright install chromium

# Copy app
COPY . .

# Environment
ENV HEADLESS=true
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
