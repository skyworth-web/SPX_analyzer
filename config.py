import os

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'trader')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')

SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Analyzer settings
DEFAULT_REFRESH_INTERVAL = 30  # seconds
MAX_LOG_ENTRIES = 1000

# Timezone
TIMEZONE = 'America/New_York'