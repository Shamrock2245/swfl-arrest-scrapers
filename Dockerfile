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
# (Puppeteer downloads its own Chromium, but needs these system libs)
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
COPY package.json ./

# Install Node dependencies
RUN npm install --omit=dev

# Copy application code (excludes items in .dockerignore)
COPY index.js run_all_counties.js ./
COPY config/ ./config/
COPY jobs/ ./jobs/
COPY normalizers/ ./normalizers/
COPY scrapers/*.js ./scrapers/
COPY shared/ ./shared/
COPY writers/ ./writers/
COPY slack/ ./slack/
COPY wix_integration/ ./wix_integration/

# Environment
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false
ENV NODE_ENV=production

# Default: run all counties. Override with docker run ... node index.js collier
CMD ["node", "index.js"]
