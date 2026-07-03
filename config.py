import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'dev-secret-key-change-in-production'
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        if DATABASE_URL.startswith('mysql://'):
            DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://', 1)
        elif DATABASE_URL.startswith('mariadb://'):
            DATABASE_URL = DATABASE_URL.replace('mariadb://', 'mysql+pymysql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///magic_memories.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    GENERATED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generations')
    
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # === PAYPAL (Mar 2026) ===
    PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'live')
    if PAYPAL_MODE == 'sandbox':
        PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_SANDBOX_CLIENT_ID', os.environ.get('PAYPAL_CLIENT_ID', ''))
        PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_SANDBOX_SECRET', os.environ.get('PAYPAL_CLIENT_SECRET', ''))
        PAYPAL_API_BASE = 'https://api-m.sandbox.paypal.com'
    else:
        PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
        PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
        PAYPAL_API_BASE = 'https://api-m.paypal.com'

    # === PRODUCT PRICING ===
    # Product 1: Quick Stories Digital + PDF ($13 — $2 less than print)
    QS_DIGITAL_BASE_PRICE = 1300
    # Product 2: Express eBook ($6)
    EBOOK_BASE_PRICE = 600
    # Product 2b: Universos Illustrated eBook ($9)
    UNIVERSOS_EBOOK_PRICE = 900
    EBOOK_EXPIRY_DAYS = 180
    # Product 3: Libros Personalizados — PDF Imprimible ($24)
    PERSONALIZED_BASE_PRICE = 2400
    PERSONALIZED_PDF_PRICE = 2400
    # Product 4: QS Printed Book (Cloudprinter, magazine_sas_a4_p_fc) — $15 + shipping
    QS_PRINT_BASE_PRICE = 1500
    # Product 5: CP Personalized Book (Cloudprinter casewrap hardcover photobook_cw_a4_p_fc) — $26 + shipping
    CP_PB_BASE_PRICE = 2600

    # Launch promotion discount (applies to product prices, NOT to shipping)
    LAUNCH_DISCOUNT_PCT = 10

    SUPPORTED_LANGUAGES = ['es', 'en']
    DEFAULT_LANGUAGE = 'en'
