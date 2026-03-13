# =============================================================================
# SWFL Arrest Scrapers - Python Scrapers (DrissionPage + Chromium)
# Runs: Charlotte, Hendry, Manatee, Sarasota, Hillsborough, Palm Beach + more
# =============================================================================

FROM python:3.11-slim

# Set timezone
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install Chromium and system dependencies for DrissionPage
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    xdg-utils \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Tell DrissionPage where to find Chromium
ENV CHROME_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Copy project files
COPY pyproject.toml /app/
COPY core/ /app/core/
COPY counties/ /app/counties/
COPY scripts/ /app/scripts/
COPY python_scrapers/ /app/python_scrapers/
COPY config/ /app/config/

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    DrissionPage>=4.0 \
    google-auth>=2.0 \
    google-auth-oauthlib>=1.0 \
    google-api-python-client>=2.0 \
    gspread>=5.0 \
    python-dotenv>=1.0 \
    pyyaml>=6.0 \
    requests>=2.28 \
    beautifulsoup4>=4.12

# Add project root to Python path
ENV PYTHONPATH=/app

# Environment
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# Default: run the county runner
CMD ["python", "scripts/run_county.py"]
