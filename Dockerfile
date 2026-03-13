# =============================================================================
# SWFL Arrest Scrapers - Node.js Scrapers
# Runs: Collier, Charlotte, Sarasota, Hendry, DeSoto, Manatee (JS versions)
# =============================================================================

FROM node:18-slim

# Set timezone
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install Chromium dependencies for Puppeteer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
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
    && rm -rf /var/lib/apt/lists/*

# Copy package files first (layer caching optimization)
COPY package.json package-lock.json ./

# Install Node dependencies
RUN npm ci --omit=dev

# Copy application code
COPY index.js ./
COPY config/ ./config/
COPY jobs/ ./jobs/
COPY scrapers/ ./scrapers/
COPY slack/ ./slack/

# Environment
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false
ENV NODE_ENV=production

# Default: run all counties
CMD ["node", "index.js"]
