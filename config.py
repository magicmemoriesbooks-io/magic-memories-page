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
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
    PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')
    PAYPAL_API_BASE = 'https://api-m.sandbox.paypal.com' if os.environ.get('PAYPAL_MODE', 'sandbox') == 'sandbox' else 'https://api-m.paypal.com'

    # === PRODUCT PRICING ===
    # Product 1: Quick Stories Digital + PDF ($20)
    QS_DIGITAL_BASE_PRICE = 2000
    # Product 2: Quick Stories / eBook ($7)
    EBOOK_BASE_PRICE = 700
    EBOOK_EXPIRY_DAYS = 180
    # Product 3: Libros Personalizados base ($30)
    PERSONALIZED_BASE_PRICE = 3000
    # Product 4: Print base price (used in /print-order)
    QS_PRINT_BASE_PRICE = 2000
    
    SUPPORTED_LANGUAGES = ['es', 'en']
    DEFAULT_LANGUAGE = 'en'
