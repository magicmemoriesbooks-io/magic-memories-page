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
    
    PADDLE_API_KEY = os.environ.get('PADDLE_SERVER_API_KEY') or os.environ.get('PADDLE_API_KEY')
    PADDLE_SELLER_ID = os.environ.get('PADDLE_SELLER_ID')
    PADDLE_CLIENT_TOKEN = os.environ.get('PADDLE_CLIENT_TOKEN')
    PADDLE_WEBHOOK_SECRET = os.environ.get('PADDLE_WEBHOOK_SECRET')
    PADDLE_ENVIRONMENT = os.environ.get('PADDLE_ENVIRONMENT', 'sandbox')
    
    # === PADDLE DYNAMIC PRICING (Feb 2026) ===
    # 
    # Product 1: Quick Stories Digital + PDF Imprimible ($20 fijo, NO va a Lulu)
    PADDLE_QS_DIGITAL_PRODUCT_ID = os.environ.get('PADDLE_QS_DIGITAL_PRODUCT_ID', '')
    _qs_digital_price = os.environ.get('PADDLE_QS_DIGITAL_PRICE_ID', '')
    PADDLE_QS_DIGITAL_PRICE_ID = _qs_digital_price if _qs_digital_price.startswith('pri_') else 'pri_01kgpq0455g6ztxfy52pcm94sg'
    QS_DIGITAL_BASE_PRICE = 2000
    #
    # Product 2: Quick Stories Impreso 12 páginas ($20 base + Lulu dinámico)
    PADDLE_QS_PRINT_PRODUCT_ID = os.environ.get('PADDLE_QS_PRINT_PRODUCT_ID', '')
    QS_PRINT_BASE_PRICE = 2000
    #
    # Product 3: Libros Personalizados Impreso 24 páginas tapa dura ($30 base + Lulu dinámico)
    PADDLE_PERSONALIZED_PRODUCT_ID = os.environ.get('PADDLE_PERSONALIZED_PRODUCT_ID', '')
    PERSONALIZED_BASE_PRICE = 3000
    #
    # Product 4: eBook Interactivo (visor flipbook) $7 fijo, sin impresión
    PADDLE_EBOOK_PRODUCT_ID = os.environ.get('PADDLE_EBOOK_PRODUCT_ID', '')
    PADDLE_EBOOK_PRICE_ID = os.environ.get('PADDLE_EBOOK_PRICE_ID', '')
    EBOOK_BASE_PRICE = 700
    EBOOK_EXPIRY_DAYS = 180
    
    SUPPORTED_LANGUAGES = ['es', 'en']
    DEFAULT_LANGUAGE = 'en'
