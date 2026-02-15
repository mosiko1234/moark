# 🔒 העברת חבילות PyPI לרשת פנימית מבודדת

## סקירה כללית

מדריך זה מסביר כיצד להעביר את חבילות moark לרשת פנימית מבודדת (air-gapped) כדי שמפתחים יוכלו להתקין אותן באמצעות `pip install`.

---

## אפשרות 1: שרת PyPI פנימי (מומלץ)

### שלב 1: בניית החבילות ברשת האינטרנט

```bash
# התקן כלי בנייה
pip install build twine

# בנה את moark-pack
cd moark-pack
python -m build
cd ..

# בנה את moark-ingest
cd moark-ingest
python -m build
cd ..
```

זה יצור:
- `moark-pack/dist/moark_pack-0.1.0-py3-none-any.whl`
- `moark-pack/dist/moark-pack-0.1.0.tar.gz`
- `moark-ingest/dist/moark_ingest-0.1.0-py3-none-any.whl`
- `moark-ingest/dist/moark-ingest-0.1.0.tar.gz`

### שלב 2: הורדת כל ה-Dependencies

```bash
# צור תיקייה לכל ה-wheels
mkdir -p pypi-packages

# הורד את moark-pack וכל ה-dependencies שלו
pip download moark-pack[ui] -d pypi-packages/

# הורד את moark-ingest וכל ה-dependencies שלו
pip download moark-ingest[ui] -d pypi-packages/

# העתק גם את החבילות שבנית
cp moark-pack/dist/*.whl pypi-packages/
cp moark-ingest/dist/*.whl pypi-packages/
```

### שלב 3: ארוז הכל ל-USB

```bash
# צור ארכיון
tar -czf moark-pypi-packages.tar.gz pypi-packages/

# או צור ZIP
zip -r moark-pypi-packages.zip pypi-packages/
```

### שלב 4: העבר לרשת הפנימית

1. העתק את `moark-pypi-packages.tar.gz` ל-USB
2. העבר פיזית לרשת הפנימית
3. חלץ את הקבצים

### שלב 5: הגדרת PyPI Server פנימי

#### אפשרות A: pypiserver (פשוט)

```bash
# ברשת הפנימית - התקן pypiserver
pip install pypiserver

# חלץ את החבילות
tar -xzf moark-pypi-packages.tar.gz

# הרץ את השרת
pypiserver run -p 8080 ./pypi-packages
```

עכשיו מפתחים יוכלו להתקין:

```bash
pip install moark-pack[ui] --index-url http://pypi-server.internal:8080/simple/
pip install moark-ingest[ui] --index-url http://pypi-server.internal:8080/simple/
```

#### אפשרות B: devpi (מתקדם יותר)

```bash
# התקן devpi
pip install devpi-server devpi-web

# אתחל
devpi-init

# הרץ
devpi-server --start

# העלה חבילות
devpi use http://localhost:3141
devpi login root --password=''
devpi index -c prod
devpi use prod
devpi upload pypi-packages/*.whl
```

#### אפשרות C: Artifactory / Nexus (ארגוני)

אם יש לך Artifactory או Nexus:

1. צור PyPI repository
2. העלה את כל הקבצים מ-`pypi-packages/`
3. הגדר את ה-URL ב-pip

---

## אפשרות 2: התקנה ישירה מ-Wheels (פשוט יותר)

### שלב 1: בניית החבילות והורדת Dependencies

```bash
# בנה את החבילות
cd moark-pack && python -m build && cd ..
cd moark-ingest && python -m build && cd ..

# צור תיקייה
mkdir -p offline-install

# הורד את כל ה-dependencies
pip download moark-pack[ui] -d offline-install/
pip download moark-ingest[ui] -d offline-install/

# העתק את החבילות שבנית
cp moark-pack/dist/*.whl offline-install/
cp moark-ingest/dist/*.whl offline-install/
```

### שלב 2: צור סקריפט התקנה

```bash
cat > offline-install/install.sh << 'EOF'
#!/bin/bash

echo "🔧 Installing moark packages offline..."

# התקן את כל החבילות מהתיקייה המקומית
pip install --no-index --find-links=. moark-pack[ui]
pip install --no-index --find-links=. moark-ingest[ui]

echo "✅ Installation complete!"
echo ""
echo "Test the installation:"
echo "  moark-pack --help"
echo "  moark-ingest --help"
EOF

chmod +x offline-install/install.sh
```

### שלב 3: ארוז והעבר

```bash
tar -czf moark-offline-install.tar.gz offline-install/
```

### שלב 4: התקנה ברשת הפנימית

```bash
# חלץ
tar -xzf moark-offline-install.tar.gz
cd offline-install

# התקן
./install.sh

# או ידנית:
pip install --no-index --find-links=. moark-pack[ui]
pip install --no-index --find-links=. moark-ingest[ui]
```

---

## אפשרות 3: pip.conf קבוע

### הגדרת pip לשימוש בשרת פנימי

צור קובץ `~/.pip/pip.conf` (Linux/Mac) או `%APPDATA%\pip\pip.ini` (Windows):

```ini
[global]
index-url = http://pypi-server.internal:8080/simple/
trusted-host = pypi-server.internal
```

עכשיו מפתחים יוכלו פשוט להריץ:

```bash
pip install moark-pack[ui]
pip install moark-ingest[ui]
```

---

## סקריפט אוטומטי מלא

צור קובץ `prepare-airgap-pypi.sh`:

```bash
#!/bin/bash

echo "🔧 Preparing moark packages for air-gapped network..."

# צבעים
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
pip download moark-pack[ui] -d airgap-pypi/packages/
pip download moark-ingest[ui] -d airgap-pypi/packages/

# 4. העתק את החבילות שבנית
echo -e "${BLUE}Step 4: Copying built packages...${NC}"
cp moark-pack/dist/*.whl airgap-pypi/packages/
cp moark-ingest/dist/*.whl airgap-pypi/packages/

# 5. צור README
cat > airgap-pypi/README.md << 'EOFREADME'
# moark Air-Gapped Installation

## Option 1: Direct Installation

```bash
cd packages
pip install --no-index --find-links=. moark-pack[ui]
pip install --no-index --find-links=. moark-ingest[ui]
```

## Option 2: Run PyPI Server

```bash
# Install pypiserver (if not already installed)
pip install pypiserver

# Run server
pypiserver run -p 8080 ./packages

# In another terminal or on other machines:
pip install moark-pack[ui] --index-url http://localhost:8080/simple/
pip install moark-ingest[ui] --index-url http://localhost:8080/simple/
```

## Verify Installation

```bash
moark-pack --help
moark-ingest --help
moark-mapping --help
```
EOFREADME

# 6. צור סקריפט התקנה
cat > airgap-pypi/install.sh << 'EOFINSTALL'
#!/bin/bash
cd packages
pip install --no-index --find-links=. moark-pack[ui]
pip install --no-index --find-links=. moark-ingest[ui]
echo "✅ Installation complete!"
EOFINSTALL

chmod +x airgap-pypi/install.sh

# 7. צור סקריפט להרצת PyPI server
cat > airgap-pypi/run-pypi-server.sh << 'EOFSERVER'
#!/bin/bash
echo "🚀 Starting PyPI server on port 8080..."
echo "Packages will be available at: http://localhost:8080/simple/"
echo ""
echo "To install packages, run:"
echo "  pip install moark-pack[ui] --index-url http://localhost:8080/simple/"
echo "  pip install moark-ingest[ui] --index-url http://localhost:8080/simple/"
echo ""
pypiserver run -p 8080 ./packages
EOFSERVER

chmod +x airgap-pypi/run-pypi-server.sh

# 8. ארוז הכל
echo -e "${BLUE}Step 5: Creating archive...${NC}"
tar -czf moark-airgap-pypi.tar.gz airgap-pypi/

# 9. סיכום
echo -e "${GREEN}✅ Done!${NC}"
echo ""
echo "Created: moark-airgap-pypi.tar.gz"
echo "Size: $(du -h moark-airgap-pypi.tar.gz | cut -f1)"
echo ""
echo "Next steps:"
echo "1. Copy moark-airgap-pypi.tar.gz to USB drive"
echo "2. Transfer to air-gapped network"
echo "3. Extract: tar -xzf moark-airgap-pypi.tar.gz"
echo "4. Run: cd airgap-pypi && ./install.sh"
echo "   OR"
echo "   Run: cd airgap-pypi && ./run-pypi-server.sh"
```

---

## שימוש מהיר

```bash
# ברשת האינטרנט
chmod +x prepare-airgap-pypi.sh
./prepare-airgap-pypi.sh

# העתק את moark-airgap-pypi.tar.gz ל-USB
# העבר לרשת הפנימית

# ברשת הפנימית
tar -xzf moark-airgap-pypi.tar.gz
cd airgap-pypi

# אפשרות 1: התקנה ישירה
./install.sh

# אפשרות 2: הרץ PyPI server
./run-pypi-server.sh
```

---

## פתרון בעיות

### "No matching distribution found"

וודא שהורדת את כל ה-dependencies:
```bash
pip download moark-pack[ui] -d packages/
```

### "Could not find a version that satisfies the requirement"

וודא שאתה משתמש ב-Python 3.10+:
```bash
python --version
```

### PyPI server לא נגיש

וודא שהפורט פתוח:
```bash
netstat -an | grep 8080
```

---

## המלצות

1. **לסביבת פיתוח**: השתמש ב-pypiserver (אפשרות 1)
2. **להתקנה חד-פעמית**: השתמש בהתקנה ישירה (אפשרות 2)
3. **לארגון גדול**: השתמש ב-Artifactory/Nexus

---

**נוצר עבור: Moses in the Ark**  
**גרסה:** 1.0  
**תאריך:** דצמבר 2024
