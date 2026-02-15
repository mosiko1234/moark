# 🔒 העברת חבילות moark לרשת פנימית מבודדת

## תהליך מהיר

### ברשת האינטרנט (שלב 1)

```bash
# הרץ את הסקריפט האוטומטי
./prepare-airgap-pypi.sh
```

זה יצור קובץ: `moark-airgap-pypi.tar.gz`

### העברה פיזית (שלב 2)

1. העתק את `moark-airgap-pypi.tar.gz` ל-USB
2. הליכה פיזית לרשת הפנימית 🚶

### ברשת הפנימית (שלב 3)

```bash
# חלץ את הקבצים
tar -xzf moark-airgap-pypi.tar.gz
cd airgap-pypi

# בחר אחת משתי האפשרויות:
```

#### אפשרות א': התקנה ישירה (למחשב בודד)

```bash
./install.sh
```

#### אפשרות ב': שרת PyPI פנימי (לכל הצוות)

```bash
./run-pypi-server.sh
```

אז כל מפתח יוכל להתקין:

```bash
pip install moark-pack[ui] --index-url http://SERVER_IP:8080/simple/
pip install moark-ingest[ui] --index-url http://SERVER_IP:8080/simple/
```

---

## הסבר מפורט

### מה הסקריפט עושה?

1. **בונה את החבילות** - יוצר wheel files
2. **מוריד dependencies** - כל החבילות הנדרשות מ-PyPI
3. **אורז הכל** - יוצר ארכיון אחד עם הכל
4. **יוצר סקריפטים** - התקנה והרצת שרת

### מה נמצא בארכיון?

```
airgap-pypi/
├── packages/              # כל החבילות (moark + dependencies)
├── install.sh            # סקריפט התקנה ישירה
├── run-pypi-server.sh    # סקריפט להרצת שרת PyPI
├── pip.conf.example      # דוגמה להגדרת pip
├── README.md             # הוראות באנגלית
└── PACKAGES.txt          # רשימת כל החבילות
```

---

## שימוש מתקדם

### הגדרת pip קבועה

אם אתה מריץ שרת PyPI פנימי, תוכל להגדיר את pip לשימוש קבוע:

**Linux/Mac:**
```bash
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = http://pypi-server.internal:8080/simple/
trusted-host = pypi-server.internal
EOF
```

**Windows:**
```cmd
mkdir %APPDATA%\pip
notepad %APPDATA%\pip\pip.ini
```

הוסף:
```ini
[global]
index-url = http://pypi-server.internal:8080/simple/
trusted-host = pypi-server.internal
```

אחרי זה, פשוט:
```bash
pip install moark-pack[ui]
pip install moark-ingest[ui]
```

### הרצת שרת PyPI כ-Service

**systemd (Linux):**

```bash
sudo cat > /etc/systemd/system/pypi-server.service << EOF
[Unit]
Description=Internal PyPI Server
After=network.target

[Service]
Type=simple
User=pypi
WorkingDirectory=/opt/airgap-pypi
ExecStart=/usr/local/bin/pypi-server run -p 8080 ./packages
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable pypi-server
sudo systemctl start pypi-server
```

---

## פתרון בעיות

### "No matching distribution found"

**בעיה:** pip לא מוצא את החבילה

**פתרון:**
```bash
# וודא שאתה בתיקייה הנכונה
cd airgap-pypi/packages

# התקן עם --no-index
pip install --no-index --find-links=. moark-pack[ui]
```

### "Could not find a version that satisfies the requirement"

**בעיה:** גרסת Python לא תואמת

**פתרון:**
```bash
# בדוק גרסת Python
python --version

# צריך Python 3.10 ומעלה
# אם יש לך Python ישן, שדרג אותו
```

### השרת לא נגיש ממחשבים אחרים

**בעיה:** לא יכול להתחבר לשרת מרחוק

**פתרון:**
```bash
# 1. בדוק שהשרת רץ
netstat -an | grep 8080

# 2. בדוק firewall
sudo ufw allow 8080

# 3. הרץ את השרת על כל הממשקים
pypiserver run -p 8080 --host 0.0.0.0 ./packages
```

### "Permission denied"

**בעיה:** אין הרשאות להתקנה

**פתרון:**
```bash
# התקן ב-user mode
pip install --user --no-index --find-links=. moark-pack[ui]

# או השתמש ב-virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# או: venv\Scripts\activate  # Windows
pip install --no-index --find-links=. moark-pack[ui]
```

---

## שאלות נפוצות

### כמה מקום צריך?

בערך 50-100 MB לכל החבילות והתלויות.

### האם צריך אינטרנט ברשת הפנימית?

לא! זה בדיוק הרעיון - הכל עובד offline.

### איך מעדכנים לגרסה חדשה?

1. ברשת האינטרנט - הרץ שוב את `prepare-airgap-pypi.sh`
2. העבר את הקובץ החדש
3. חלץ ו-install שוב

### האם אפשר להתקין רק את moark-ingest?

כן! בתיקיית packages:
```bash
pip install --no-index --find-links=. moark-ingest[ui]
```

### איך מוודאים שההתקנה הצליחה?

```bash
# בדוק שהפקודות עובדות
moark-pack --help
moark-ingest --help
moark-mapping --help

# בדוק גרסה
pip show moark-pack
pip show moark-ingest
```

---

## המלצות

### לסביבת פיתוח קטנה (2-5 מפתחים)
✅ השתמש בהתקנה ישירה (`./install.sh`)

### לצוות בינוני (5-20 מפתחים)
✅ הרץ שרת PyPI פנימי (`./run-pypi-server.sh`)

### לארגון גדול (20+ מפתחים)
✅ השתמש ב-Artifactory או Nexus Repository

---

## תמיכה

לשאלות ותמיכה: **משה אליה**

---

**גרסה:** 1.0  
**תאריך:** דצמבר 2024  
**חלק ממערכת:** Moses in the Ark ⛵
