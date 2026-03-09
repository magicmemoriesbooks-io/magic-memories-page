# GUIA DE INSTALACION EN EL VPS
## Magic Memories Books - Paso a paso para principiantes

---

## QUE HAY EN CADA ZIP

| ZIP | Que contiene | Para que sirve |
|-----|-------------|---------------|
| **core.zip** | Los archivos principales del programa (app.py, config.py, etc.) | Es el "cerebro" de la web |
| **services_templates.zip** | La logica de los cuentos + las paginas HTML | Todo lo que se ve y lo que genera cuentos |
| **static.zip** | Imagenes, fuentes de texto, sonidos | Lo visual de la web (logos, iconos, portadas) |
| **visores.zip** | Los 3 visores de libros (flipbook) | Para que los clientes vean sus eBooks |
| **docs.zip** | Documentacion interna (opcional) | Solo para referencia, no es necesario para funcionar |

---

## ANTES DE EMPEZAR

Necesitas tener a mano:

1. **Acceso al VPS** (la IP y tu contraseña de SSH)
2. **Los 5 archivos ZIP** descargados en tu computadora
3. **Tus datos de las APIs** (los mismos que ya tienes configurados):
   - OpenAI API Key
   - Replicate API Token
   - Paddle: API Key, Seller ID, Client Token, Webhook Secret, y los IDs de productos/precios
   - Lulu: Client Key y Secret (sandbox y/o produccion)
   - Email: contraseña de aplicacion de Gmail
4. **FileZilla** instalado (programa gratis para subir archivos) - descargalo de https://filezilla-project.org/

---

## PASO A PASO

### PASO 1: Conectar al VPS

Abre la terminal (en Mac) o PowerShell (en Windows) y escribe:

```
ssh root@TU_IP_DEL_VPS
```

Te pedira la contraseña. Escribela (no se ve mientras escribes, es normal) y dale Enter.

---

### PASO 2: Parar el servicio actual

```
sudo systemctl stop magicmemories
```

Esto apaga la web temporalmente. Es normal, la volveremos a encender al final.

---

### PASO 3: Hacer una copia de seguridad

Esto guarda una copia de la version anterior por si acaso:

```
cd /var/www
sudo cp -r magic-memories magic-memories-backup-$(date +%Y%m%d)
```

Ahora tienes una carpeta de respaldo con la fecha de hoy.

---

### PASO 4: Subir los 5 ZIP al VPS

**Opcion A: Con FileZilla (mas facil)**

1. Abre FileZilla
2. Arriba, donde dice "Servidor", pon la IP de tu VPS
3. "Nombre de usuario": root
4. "Contraseña": tu contraseña
5. "Puerto": 22
6. Dale a "Conexion rapida"
7. En el lado DERECHO (el VPS), navega a `/var/www/magic-memories/`
8. En el lado IZQUIERDO (tu computadora), busca donde tienes los 5 ZIP
9. Arrastra los 5 ZIP al lado derecho

**Opcion B: Con la terminal (si ya estas conectada por SSH desde otra ventana)**

Abre OTRA terminal (sin cerrar la del SSH) y escribe:

```
scp core.zip services_templates.zip static.zip visores.zip docs.zip root@TU_IP_DEL_VPS:/var/www/magic-memories/
```

---

### PASO 5: Descomprimir los ZIP (en la terminal del VPS)

Vuelve a la terminal donde tienes el SSH abierto y escribe estos comandos uno por uno:

```
cd /var/www/magic-memories

sudo unzip -o core.zip
sudo unzip -o services_templates.zip
sudo unzip -o static.zip
sudo unzip -o visores.zip
sudo unzip -o docs.zip
```

El `-o` significa que sobreescribe los archivos viejos sin preguntar.

Luego limpia los ZIP (ya no los necesitas ahi):

```
rm -f core.zip services_templates.zip static.zip visores.zip docs.zip
```

---

### PASO 6: Configurar el archivo .env

Este es el paso MAS IMPORTANTE. Aqui pones todos tus datos reales.

```
sudo cp .env.example .env
sudo nano .env
```

Se abrira un editor de texto. Recorre el archivo y cambia cada linea con tus datos reales.

**Las variables mas importantes que debes cambiar:**

| Variable | Que poner | Ejemplo |
|----------|-----------|---------|
| `DATABASE_URL` | Los datos de tu base de datos MySQL | `mysql+pymysql://magicuser:mipassword@localhost/magicmemories` |
| `SESSION_SECRET` | Una cadena aleatoria larga | Genera una con el comando que dice en el archivo |
| `OPENAI_API_KEY` | Tu clave de OpenAI | `sk-proj-abc123...` |
| `REPLICATE_API_TOKEN` | Tu token de Replicate | `r8_abc123...` |
| `PADDLE_ENVIRONMENT` | `sandbox` para pruebas, `production` para cobrar de verdad | `production` |
| `PADDLE_API_KEY` | Tu API key de Paddle | `pdl_abc123...` |
| `PADDLE_SELLER_ID` | Tu Seller ID de Paddle | El numero que te da Paddle |
| `PADDLE_CLIENT_TOKEN` | Tu Client Token de Paddle | `ctok_abc123...` |
| `PADDLE_WEBHOOK_SECRET` | Tu Webhook Secret de Paddle | `pdl_ntfset_abc123...` |
| `PADDLE_QS_DIGITAL_PRICE_ID` | ID del precio Quick Stories Digital | `pri_abc123...` |
| `PADDLE_QS_DIGITAL_PRODUCT_ID` | ID del producto Quick Stories Digital | `pro_abc123...` |
| `PADDLE_QS_PRINT_PRODUCT_ID` | ID del producto Quick Stories Impreso | `pro_abc123...` |
| `PADDLE_PERSONALIZED_PRODUCT_ID` | ID del producto Libros Personalizados | `pro_abc123...` |
| `PADDLE_EBOOK_PRODUCT_ID` | ID del producto eBook | `pro_abc123...` |
| `PADDLE_EBOOK_PRICE_ID` | ID del precio eBook | `pri_abc123...` |
| `LULU_USE_SANDBOX` | `true` para pruebas, `false` para impresion real | `false` |
| `LULU_CLIENT_KEY` | Tu Client Key de Lulu (produccion) | La que te dio Lulu |
| `LULU_CLIENT_SECRET` | Tu Client Secret de Lulu (produccion) | La que te dio Lulu |
| `SMTP_PASSWORD` | Contraseña de aplicacion de Gmail | La que generaste en Google |
| `ADMIN_PASSWORD` | Contraseña para el panel /admin | La que tu quieras |

Para guardar en nano: pulsa **Ctrl+O**, luego **Enter**, luego **Ctrl+X** para salir.

---

### PASO 7: Ejecutar el instalador

```
cd /var/www/magic-memories
chmod +x deploy.sh
sudo bash deploy.sh
```

Esto instala todas las dependencias automaticamente. Espera a que termine (puede tardar 1-2 minutos).

---

### PASO 8: Configurar el servicio

```
sudo cp magicmemories.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable magicmemories
```

---

### PASO 9: Dar permisos al usuario de la web

```
sudo chown -R www-data:www-data /var/www/magic-memories
```

---

### PASO 10: Encender la web

```
sudo systemctl start magicmemories
```

Espera 5 segundos y comprueba que esta funcionando:

```
sudo systemctl status magicmemories
```

Deberias ver algo como `Active: active (running)` en color verde.

---

### PASO 11: Verificar que funciona

Abre tu navegador y visita:

1. `https://www.magicmemoriesbooks.com` — Deberia cargar la pagina principal
2. `https://www.magicmemoriesbooks.com/faq` — Deberia mostrar las preguntas frecuentes
3. `https://www.magicmemoriesbooks.com/admin` — Deberia pedir contraseña del admin

---

## CAMBIAR DE SANDBOX A PRODUCCION

Cuando hayas probado que todo funciona y quieras empezar a cobrar de verdad:

1. Edita el archivo .env: `sudo nano /var/www/magic-memories/.env`
2. Cambia estas dos lineas:
   ```
   PADDLE_ENVIRONMENT=production
   LULU_USE_SANDBOX=false
   ```
3. Asegurate de que los IDs de productos/precios de Paddle son los de PRODUCCION (no los de sandbox)
4. Asegurate de que `LULU_CLIENT_KEY` y `LULU_CLIENT_SECRET` son las credenciales de produccion
5. Guarda y reinicia: `sudo systemctl restart magicmemories`

---

## SI ALGO SALE MAL

### La web no carga
```
sudo systemctl status magicmemories
sudo journalctl -u magicmemories -n 50
```
El segundo comando muestra las ultimas 50 lineas del log. Busca errores en rojo.

### Error de base de datos
Verifica que MySQL esta corriendo:
```
sudo systemctl status mysql
```
Y que los datos en `DATABASE_URL` son correctos (usuario, contraseña, nombre de la base de datos).

### Error de permisos
```
sudo chown -R www-data:www-data /var/www/magic-memories
sudo chmod -R 777 /var/www/magic-memories/generated /var/www/magic-memories/uploads /var/www/magic-memories/logs /var/www/magic-memories/generations /var/www/magic-memories/lulu_orders
```

### Quiero volver a la version anterior
```
sudo systemctl stop magicmemories
sudo rm -rf /var/www/magic-memories
sudo mv /var/www/magic-memories-backup-FECHA /var/www/magic-memories
sudo systemctl start magicmemories
```
(Cambia FECHA por la fecha del backup, la puedes ver con `ls /var/www/`)

### Los pagos no funcionan
- Verifica que `PADDLE_ENVIRONMENT` es `production` (no `sandbox`)
- Verifica que todos los IDs de productos y precios (`pro_...`, `pri_...`) son los de produccion
- Verifica que el `PADDLE_WEBHOOK_SECRET` es correcto
- En el panel de Paddle, verifica que la URL del webhook apunta a `https://www.magicmemoriesbooks.com/webhook/paddle`

### Las imagenes no se generan
- Verifica que `REPLICATE_API_TOKEN` es correcto
- Verifica que tienes credito en tu cuenta de Replicate

### Los emails no llegan
- Verifica que `SMTP_PASSWORD` es una "contraseña de aplicacion" de Google (no tu contraseña normal de Gmail)
- Verifica que `SENDER_EMAIL` es correcto

---

## QUE HAY DE NUEVO (respecto a la version anterior)

- Todos los emails del cliente ahora tienen el mismo diseño bonito (gradiente morado-rosa)
- Terminos y Condiciones actualizados (aranceles, reembolso por fallo persistente, alucinaciones de IA)
- Politica de Privacidad corregida (numeracion)
- Advertencia de verificar email antes de crear cuentos
- Footer mejorado con links a pagina de contacto
- Pagina de contacto con formulario por departamento
- Eliminado fallback hardcodeado de Paddle (ahora usa solo tus variables de entorno)
