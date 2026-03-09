#!/bin/bash

echo "==========================================="
echo " Magic Memories Books - Despliegue en VPS"
echo " Hetzner 4 vCPU / 8GB RAM"
echo "==========================================="
echo ""

PROJECT_DIR="/var/www/magic-memories"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: No se encontró el directorio $PROJECT_DIR"
    echo "Crea el directorio primero: sudo mkdir -p $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

echo "1/7 - Instalando dependencias del sistema..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv nginx ghostscript

echo ""
echo "2/7 - Creando directorios de datos..."
mkdir -p generated uploads media logs lulu_orders story_previews generations
mkdir -p generations/pdfs generations/epubs generations/email generations/lulu
mkdir -p generations/visor_pb generations/visor_qs
mkdir -p generated/uploads/furry_photos
mkdir -p static/temp_stories static/uploads
mkdir -p visor/biblioteca visor_pb/biblioteca visor_qs/biblioteca

echo ""
echo "3/7 - Configurando entorno virtual de Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   Entorno virtual creado"
else
    echo "   Entorno virtual ya existe"
fi
source venv/bin/activate

echo ""
echo "4/7 - Instalando dependencias de Python..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "   Dependencias instaladas"

echo ""
echo "5/7 - Verificando archivo .env..."
if [ ! -f ".env" ]; then
    echo "   ADVERTENCIA: No se encontró archivo .env"
    echo "   Copia el ejemplo y edítalo con tus datos:"
    echo "   cp .env.example .env"
    echo "   nano .env"
else
    echo "   .env encontrado"
fi

echo ""
echo "6/7 - Configurando permisos..."
chmod -R 755 static/
chmod -R 777 generated/ uploads/ media/ logs/ lulu_orders/ story_previews/ generations/
chmod +x deploy.sh

echo ""
echo "7/7 - Limpiando archivos temporales..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

echo ""
echo "==========================================="
echo " CONFIGURACION COMPLETADA"
echo "==========================================="
echo ""
echo "SIGUIENTE PASO: Configurar el servicio systemd"
echo ""
echo "  sudo cp magicmemories.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable magicmemories"
echo "  sudo systemctl start magicmemories"
echo ""
echo "Para ver los logs en tiempo real:"
echo "  sudo journalctl -u magicmemories -f"
echo ""
echo "Para reiniciar después de cambios:"
echo "  sudo systemctl restart magicmemories"
echo ""

echo "==========================================="
echo " CONFIGURACION NGINX (si no la tienes)"
echo "==========================================="
echo ""
echo "Crea el archivo: sudo nano /etc/nginx/sites-available/magicmemories"
echo ""
echo "Contenido recomendado:"
cat << 'NGINX_EOF'

server {
    listen 80;
    server_name www.magicmemoriesbooks.com magicmemoriesbooks.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    location /static/ {
        alias /var/www/magic-memories/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

NGINX_EOF
echo ""
echo "Luego actívalo:"
echo "  sudo ln -s /etc/nginx/sites-available/magicmemories /etc/nginx/sites-enabled/"
echo "  sudo nginx -t"
echo "  sudo systemctl reload nginx"
echo ""
echo "Para HTTPS con Let's Encrypt:"
echo "  sudo apt install certbot python3-certbot-nginx"
echo "  sudo certbot --nginx -d www.magicmemoriesbooks.com -d magicmemoriesbooks.com"
echo ""
