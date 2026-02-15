#!/bin/bash

echo "🔧 Preparing moark packages for air-gapped network..."

# צבעים
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# בדוק שהכלים הנדרשים מותקנים
echo -e "${BLUE}Checking prerequisites...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${YELLOW}Python not found. Please install Python 3.10+${NC}"
    exit 1
fi

if ! python -m pip --version &> /dev/null; then
    echo -e "${YELLOW}pip not found. Please install pip${NC}"
    exit 1
fi

# התקן build אם לא מותקן
pip install build twine --quiet

# 1. בנה את החבילות
echo -e "${BLUE}Step 1: Building packages...${NC}"
cd moark-pack && python -m build && cd ..
cd moark-ingest && python -m build && cd ..

# 2. צור תיקייה
echo -e "${BLUE}Step 2: Creating package directory...${NC}"
rm -rf airgap-pypi
mkdir -p airgap-pypi/packages

# 3. הורד dependencies
echo -e "${BLUE}Step 3: Downloading dependencies...${NC}"
echo "  - Downloading moark-pack dependencies..."
pip download moark-pack[ui] -d airgap-pypi/packages/ --quiet
echo "  - Downloading moark-ingest dependencies..."
pip download moark-ingest[ui] -d airgap-pypi/packages/ --quiet

# 4. העתק את החבילות שבנית
echo -e "${BLUE}Step 4: Copying built packages...${NC}"
cp moark-pack/dist/*.whl airgap-pypi/packages/ 2>/dev/null || true
cp moark-pack/dist/*.tar.gz airgap-pypi/packages/ 2>/dev/null || true
cp moark-ingest/dist/*.whl airgap-pypi/packages/ 2>/dev/null || true
cp moark-ingest/dist/*.tar.gz airgap-pypi/packages/ 2>/dev/null || true

# 5. צור README
cat > airgap-pypi/README.md << 'EOFREADME'
# 🔒 moark Air-Gapped Installation

## Quick Start

### Option 1: Direct Installation (Simplest)

```bash
cd packages
pip install --no-index --find-links=. moark-pack[ui]
pip install --no-index --find-links=. moark-ingest[ui]
```

Or use the install script:
```bash
./install.sh
```

### Option 2: Run Internal PyPI Server (Recommended for Teams)

```bash
# Install pypiserver (one-time setup)
pip install pypiserver

# Run server
./run-pypi-server.sh
```

Then on any machine in the network:
```bash
pip install moark-pack[ui] --index-url http://pypi-server.internal:8080/simple/
pip install moark-ingest[ui] --index-url http://pypi-server.internal:8080/simple/
```

## Verify Installation

```bash
moark-pack --help
moark-ingest --help
moark-mapping --help
```

## Package Contents

This archive contains:
- moark-pack (with all dependencies)
- moark-ingest (with all dependencies)
- All required Python packages

Total packages: $(ls packages/ | wc -l)

## Support

For questions, contact: Moshe Eliya
EOFREADME

# 6. צור סקריפט התקנה
cat > airgap-pypi/install.sh << 'EOFINSTALL'
#!/bin/bash

echo "🔧 Installing moark packages..."

cd packages

echo "Installing moark-pack..."
pip install --no-index --find-links=. moark-pack[ui]

echo "Installing moark-ingest..."
pip install --no-index --find-links=. moark-ingest[ui]

echo ""
echo "✅ Installation complete!"
echo ""
echo "Verify installation:"
echo "  moark-pack --help"
echo "  moark-ingest --help"
echo "  moark-mapping --help"
EOFINSTALL

chmod +x airgap-pypi/install.sh

# 7. צור סקריפט להרצת PyPI server
cat > airgap-pypi/run-pypi-server.sh << 'EOFSERVER'
#!/bin/bash

echo "🚀 Starting Internal PyPI Server..."
echo "=================================="
echo ""

# בדוק אם pypiserver מותקן
if ! command -v pypi-server &> /dev/null; then
    echo "Installing pypiserver..."
    pip install pypiserver
fi

echo "Server will be available at:"
echo "  http://localhost:8080/simple/"
echo ""
echo "To install packages from other machines:"
echo "  pip install moark-pack[ui] --index-url http://YOUR_SERVER_IP:8080/simple/"
echo "  pip install moark-ingest[ui] --index-url http://YOUR_SERVER_IP:8080/simple/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

pypiserver run -p 8080 ./packages
EOFSERVER

chmod +x airgap-pypi/run-pypi-server.sh

# 8. צור pip.conf לדוגמה
cat > airgap-pypi/pip.conf.example << 'EOFPIPCONF'
# Copy this file to ~/.pip/pip.conf (Linux/Mac) or %APPDATA%\pip\pip.ini (Windows)
# Replace YOUR_SERVER_IP with the actual IP address of your PyPI server

[global]
index-url = http://YOUR_SERVER_IP:8080/simple/
trusted-host = YOUR_SERVER_IP
EOFPIPCONF

# 9. צור רשימת חבילות
echo -e "${BLUE}Step 5: Creating package list...${NC}"
ls -lh airgap-pypi/packages/ > airgap-pypi/PACKAGES.txt

# 10. ארוז הכל
echo -e "${BLUE}Step 6: Creating archive...${NC}"
tar -czf moark-airgap-pypi.tar.gz airgap-pypi/

# 11. סיכום
echo ""
echo -e "${GREEN}✅ Done!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Created: moark-airgap-pypi.tar.gz${NC}"
echo "Size: $(du -h moark-airgap-pypi.tar.gz | cut -f1)"
echo "Packages: $(ls airgap-pypi/packages/ | wc -l | tr -d ' ')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next steps:"
echo "1. Copy moark-airgap-pypi.tar.gz to USB drive"
echo "2. Transfer to air-gapped network"
echo "3. Extract: tar -xzf moark-airgap-pypi.tar.gz"
echo "4. Choose installation method:"
echo ""
echo "   Option A - Direct install (single machine):"
echo "   cd airgap-pypi && ./install.sh"
echo ""
echo "   Option B - PyPI server (multiple machines):"
echo "   cd airgap-pypi && ./run-pypi-server.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
