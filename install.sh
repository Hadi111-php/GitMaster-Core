#!/bin/bash
echo "⏳ در حال نصب پیش‌نیازها..."
if [ -d "/data/data/com.termux" ]; then
    # اگر ترموکس بود
    pkg install python -y > /dev/null 2>&1
    pip install flask requests gitpython > /dev/null 2>&1
else
    # اگر کامپیوتر (لینوکس/مک) بود
    pip3 install flask requests gitpython > /dev/null 2>&1
fi
echo "✅ پیش‌نیازها نصب شدند. در حال اجرای داشبورد..."
python3 app.py
