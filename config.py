# config.py
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'the-working-man-secret-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://the_working_man_db_user:us8Ydv5MGrJXFZhbKBuW22fWMlOoBXjR@dpg-d9ngsop42hec73fjmt20-a/the_working_man_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    BCRYPT_LOG_ROUNDS = 12

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}