#!/bin/bash
set -e

echo "🚀 SWFL Arrest Scrapers - Setup Script"
echo "======================================"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version must be 18 or higher (found: $NODE_VERSION)"
    exit 1
fi

echo "✅ Node.js $(node -v) found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install
echo "✅ Dependencies installed"
echo ""

# Create directories
echo "📁 Creating directories..."
mkdir -p creds logs fixtures
echo "✅ Directories created"
echo ""

# Copy .env if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "✅ .env created"
    echo ""
    echo "⚠️  Please edit .env and add your credentials!"
else
    echo "ℹ️  .env already exists, skipping..."
fi
echo ""

# Check for credentials
if [ ! -f "creds/service-account-key.json" ]; then
    echo "⚠️  Missing: creds/service-account-key.json"
    echo ""
    echo "📋 Next steps:"
    echo "1. Get your Google service account JSON key"
    echo "2. Save it as: creds/service-account-key.json"
    echo "3. Make sure it has access to the spreadsheet"
    echo "4. Run: npm run run:collier (to test)"
else
    echo "✅ Service account key found"
    echo ""
    echo "🎉 Setup complete! You can now run:"
    echo "   npm run run:collier    # Test single county"
    echo "   npm start              # Run all counties"
fi

echo ""
echo "📖 See QUICKSTART.md for detailed instructions"
