from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    product_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    
    child_name = db.Column(db.String(100), nullable=False)
    child_gender = db.Column(db.String(20), nullable=False)
    child_age_range = db.Column(db.String(20), nullable=False)
    
    hair_color = db.Column(db.String(50))
    hair_type = db.Column(db.String(50))
    eye_color = db.Column(db.String(50))
    skin_tone = db.Column(db.String(50))
    
    story_template = db.Column(db.String(100))
    custom_story_description = db.Column(db.Text)
    dedication = db.Column(db.Text)
    author_name = db.Column(db.String(100))
    
    photos = db.Column(db.Text)
    
    customer_email = db.Column(db.String(120), nullable=False)
    customer_name = db.Column(db.String(100))
    
    paypal_order_id = db.Column(db.String(100))
    amount_paid = db.Column(db.Integer)
    
    digital_pdf_path = db.Column(db.String(255))
    print_pdf_path = db.Column(db.String(255))
    
    terms_accepted = db.Column(db.Boolean, default=False)
    photo_consent = db.Column(db.Boolean, default=False)
    
    language = db.Column(db.String(5), default='es')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class StoryTemplate(db.Model):
    __tablename__ = 'story_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name_es = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    description_es = db.Column(db.Text)
    description_en = db.Column(db.Text)
    prompt_template = db.Column(db.Text, nullable=False)
    image_style = db.Column(db.String(100), default='vibrant watercolor')
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<StoryTemplate {self.name_en}>'


class RealStoryOrder(db.Model):
    __tablename__ = 'real_story_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    
    status = db.Column(db.String(30), default='FORM_SUBMITTED')
    
    language = db.Column(db.String(5), default='es')
    target_age = db.Column(db.String(20))
    theme_type = db.Column(db.String(20))
    theme_preset = db.Column(db.String(50))
    story_purpose = db.Column(db.String(50))
    story_tone = db.Column(db.String(50))
    custom_event_description = db.Column(db.Text)
    dedication = db.Column(db.Text)
    author_name = db.Column(db.String(100))
    
    generated_story_text = db.Column(db.Text)
    approved_story_text = db.Column(db.Text)
    story_generation_prompt = db.Column(db.Text)
    
    customer_email = db.Column(db.String(120), nullable=False)
    customer_name = db.Column(db.String(100))
    
    paypal_order_id = db.Column(db.String(100))
    amount_paid = db.Column(db.Integer)
    
    digital_pdf_path = db.Column(db.String(255))
    print_pdf_path = db.Column(db.String(255))
    ebook_path = db.Column(db.String(255))
    cover_pdf_path = db.Column(db.String(255))
    
    lulu_job_id = db.Column(db.String(100))
    lulu_order_folder = db.Column(db.String(255))
    shipping_name = db.Column(db.String(200))
    shipping_street1 = db.Column(db.String(255))
    shipping_street2 = db.Column(db.String(255))
    shipping_city = db.Column(db.String(100))
    shipping_state = db.Column(db.String(100))
    shipping_postal_code = db.Column(db.String(20))
    shipping_country = db.Column(db.String(5))
    shipping_phone = db.Column(db.String(50))
    
    photos_folder = db.Column(db.String(255))
    current_task_id = db.Column(db.String(100))
    
    terms_accepted = db.Column(db.Boolean, default=False)
    photo_consent = db.Column(db.Boolean, default=False)
    photos_deleted = db.Column(db.Boolean, default=False)
    auto_expand_story = db.Column(db.Boolean, default=False)
    character_map = db.Column(db.Text)  # JSON mapping (character X) -> visual description
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    text_approved_at = db.Column(db.DateTime)
    characters_approved_at = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    email_sent_at = db.Column(db.DateTime)
    photos_cleanup_scheduled_at = db.Column(db.DateTime)
    files_purged_at = db.Column(db.DateTime)
    
    illustration_paths = db.Column(db.Text)  # Original images (for PDF after payment)
    preview_paths = db.Column(db.Text)  # Watermarked images (for gallery preview)
    cover_path = db.Column(db.Text)  # Unique cover illustration
    cover_preview_path = db.Column(db.Text)  # Watermarked cover for preview
    
    characters = db.relationship('RealStoryCharacter', backref='order', lazy=True, cascade='all, delete-orphan')
    pets = db.relationship('RealStoryPet', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<RealStoryOrder {self.order_number}>'


class RealStoryCharacter(db.Model):
    __tablename__ = 'real_story_characters'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('real_story_orders.id'), nullable=False)
    
    character_order = db.Column(db.Integer, default=1)
    
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Float)
    age_description = db.Column(db.String(50))
    relationship = db.Column(db.String(100))
    personality_trait = db.Column(db.String(50))
    clothing_description = db.Column(db.Text)
    
    hair_color = db.Column(db.String(50))
    hair_type = db.Column(db.String(50))
    hair_length = db.Column(db.String(50))
    eye_color = db.Column(db.String(50))
    skin_tone = db.Column(db.String(50))
    accessory = db.Column(db.String(200))  # Can store multiple comma-separated accessories
    facial_hair = db.Column(db.String(50))  # For adult males: stubble, short_beard, full_beard, mustache, goatee
    body_type = db.Column(db.String(50))  # delgada, media, kilos_de_mas
    height_cm = db.Column(db.Integer)  # Height in centimeters for scale reference
    distinctive_features = db.Column(db.Text)
    clothing_style = db.Column(db.String(100))
    clothing_color = db.Column(db.String(50))  # Main clothing color for consistency
    
    photo_filename = db.Column(db.String(255))
    
    base_illustration_path = db.Column(db.String(255))
    base_illustration_approved = db.Column(db.Boolean, default=False)
    
    character_prompt = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RealStoryCharacter {self.name} - {self.role}>'


class RealStoryPet(db.Model):
    __tablename__ = 'real_story_pets'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('real_story_orders.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    size = db.Column(db.String(50))
    fur_color = db.Column(db.String(100))
    fur_type = db.Column(db.String(50))
    eye_color = db.Column(db.String(50))
    distinctive_features = db.Column(db.Text)
    personality = db.Column(db.String(100))
    role_in_story = db.Column(db.String(100))
    
    photo_filename = db.Column(db.String(255))
    
    base_illustration_path = db.Column(db.String(255))
    base_illustration_approved = db.Column(db.Boolean, default=False)
    
    pet_prompt = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RealStoryPet {self.name} - {self.species}>'


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    language = db.Column(db.String(2), default='es')
    consented = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    unsubscribe_token = db.Column(db.String(64), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<NewsletterSubscriber {self.email}>'


class PreviewLead(db.Model):
    __tablename__ = 'preview_leads'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    story_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PreviewLead {self.email}>'


class PrintOrderRequest(db.Model):
    __tablename__ = 'print_order_requests'

    id = db.Column(db.Integer, primary_key=True)
    preview_id = db.Column(db.String(100), nullable=False)
    child_name = db.Column(db.String(100), nullable=True)
    customer_email = db.Column(db.String(255), nullable=False)
    paypal_order_id = db.Column(db.String(100), nullable=True)
    amount_paid = db.Column(db.Float, nullable=True)
    shipping_name = db.Column(db.String(200), nullable=True)
    shipping_street = db.Column(db.String(300), nullable=True)
    shipping_city = db.Column(db.String(100), nullable=True)
    shipping_state = db.Column(db.String(100), nullable=True)
    shipping_postal = db.Column(db.String(20), nullable=True)
    shipping_country = db.Column(db.String(10), nullable=True)
    shipping_phone = db.Column(db.String(50), nullable=True)
    shipping_method = db.Column(db.String(50), nullable=True)
    shipping_cost = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(30), default='payment_confirmed')
    lulu_print_job_id = db.Column(db.String(100), nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    tracking_email_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PrintOrderRequest {self.id} {self.customer_email}>'


class StoryBackup(db.Model):
    """Backup of story_previews/*.json files in PostgreSQL so they survive container rebuilds."""
    __tablename__ = 'story_backups'

    id = db.Column(db.Integer, primary_key=True)
    preview_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<StoryBackup {self.preview_id}>'


class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    coupon_type = db.Column(db.String(20), default='general')
    discount_pct = db.Column(db.Integer, default=20)
    owner_name = db.Column(db.String(100))
    owner_email = db.Column(db.String(120))
    commission_pct = db.Column(db.Integer, default=0)
    max_uses = db.Column(db.Integer, default=0)
    use_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Coupon {self.code}>'


class CouponLead(db.Model):
    __tablename__ = 'coupon_leads'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CouponLead {self.email}>'


class CouponUsage(db.Model):
    __tablename__ = 'coupon_usages'

    id = db.Column(db.Integer, primary_key=True)
    coupon_code = db.Column(db.String(50), nullable=False)
    buyer_email = db.Column(db.String(120))
    paypal_order_id = db.Column(db.String(100))
    discount_pct = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CouponUsage {self.coupon_code} {self.buyer_email}>'


class PhotoUploadLog(db.Model):
    """Permanent log of every photo upload — record survives 72h auto-deletion."""
    __tablename__ = 'photo_upload_log'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, index=True)
    story_id = db.Column(db.String(100))
    photo_type = db.Column(db.String(20), default='human')
    ip_address = db.Column(db.String(50))
    file_size_kb = db.Column(db.Float)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    email = db.Column(db.String(255), nullable=True)
    child_name = db.Column(db.String(100), nullable=True)
    preview_id = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<PhotoUploadLog {self.filename}>'


class CommunityStory(db.Model):
    """Solidarity storybook — free, cause-driven, bilingual."""
    __tablename__ = 'community_stories'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title_es = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    description_es = db.Column(db.Text)
    description_en = db.Column(db.Text)
    cause = db.Column(db.String(100))
    status = db.Column(db.String(20), default='draft')  # draft/published/hidden/archived
    content_version = db.Column(db.Integer, default=1)
    cover_image = db.Column(db.String(255))
    default_child_name_es = db.Column(db.String(50), default='Valeria')
    default_child_name_en = db.Column(db.String(50), default='Valeria')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pages = db.relationship('CommunityStoryPage', backref='story',
                            order_by='CommunityStoryPage.page_number', lazy='dynamic')
    downloads = db.relationship('CommunityDownload', backref='story', lazy='dynamic')

    def __repr__(self):
        return f'<CommunityStory {self.slug}>'


class CommunityStoryPage(db.Model):
    """One illustrated page inside a CommunityStory."""
    __tablename__ = 'community_story_pages'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('community_stories.id'),
                         nullable=False, index=True)
    page_number = db.Column(db.Integer, nullable=False)
    image_file = db.Column(db.String(255))
    text_top_es = db.Column(db.Text)
    text_top_en = db.Column(db.Text)
    text_center_es = db.Column(db.Text)
    text_center_en = db.Column(db.Text)
    text_bottom_es = db.Column(db.Text)
    text_bottom_en = db.Column(db.Text)
    font = db.Column(db.String(100), default='Quicksand')
    font_size = db.Column(db.Integer, default=18)
    font_color = db.Column(db.String(20), default='#FFFFFF')
    text_alignment = db.Column(db.String(10), default='center')
    text_box_x = db.Column(db.Float, default=0.05)
    text_box_y = db.Column(db.Float, default=0.72)
    text_box_width = db.Column(db.Float, default=0.90)
    text_box_height = db.Column(db.Float, default=0.24)

    def __repr__(self):
        return f'<CommunityStoryPage story={self.story_id} page={self.page_number}>'


class CommunityDownload(db.Model):
    """One download request — carries access token for viewer + PDF."""
    __tablename__ = 'community_downloads'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('community_stories.id'),
                         nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    child_name = db.Column(db.String(50))
    adult_name = db.Column(db.String(100))
    pdf_format = db.Column(db.String(10), default='A4')
    download_token = db.Column(db.String(36), unique=True, nullable=False, index=True)
    language = db.Column(db.String(5), default='es')
    ip = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    how_found_us = db.Column(db.String(100))
    downloader_type = db.Column(db.String(50))
    campaign_source = db.Column(db.String(100), default='unknown')
    utm_source = db.Column(db.String(100))
    utm_medium = db.Column(db.String(100))
    utm_campaign = db.Column(db.String(100))
    utm_content = db.Column(db.String(100))
    referrer_url = db.Column(db.String(500))
    completed_download = db.Column(db.Boolean, default=False)
    times_downloaded = db.Column(db.Integer, default=0)
    pdf_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CommunityDownload {self.email} story={self.story_id}>'


class CommunitySubscriber(db.Model):
    """Email subscriber who opted in via a Community Story."""
    __tablename__ = 'community_subscribers'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    language = db.Column(db.String(5), default='es')
    active = db.Column(db.Boolean, default=True)
    source_story = db.Column(db.String(100))
    source_campaign = db.Column(db.String(100))
    consent_version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CommunitySubscriber {self.email}>'
