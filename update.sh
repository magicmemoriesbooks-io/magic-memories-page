#!/bin/bash
APP="/home/magicbooks/app"
GH="https://raw.githubusercontent.com/magicmemoriesbooks-io/magic-memories-page/main"
echo "Actualizando Magic Memories Books..."
curl -fsSL "$GH/app.py" -o "$APP/app.py" && echo "OK app.py"
curl -fsSL "$GH/services/email_service.py" -o "$APP/services/email_service.py" && echo "OK email_service.py"
curl -fsSL "$GH/templates/formats.html" -o "$APP/templates/formats.html" && echo "OK formats.html"
curl -fsSL "$GH/templates/formats_success.html" -o "$APP/templates/formats_success.html" && echo "OK formats_success.html"
curl -fsSL "$GH/static/images/firma_isabel.jpg" -o "$APP/static/images/firma_isabel.jpg" && echo "OK firma.jpg"
systemctl restart magicbooks && sleep 3
systemctl status magicbooks --no-pager | head -5
echo "=== ACTUALIZADO ==="
