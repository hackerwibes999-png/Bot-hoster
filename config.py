import os
from dotenv import load_dotenv

# Load .env file if exists (for local development)
load_dotenv()

# Get token from environment variable (Render sets this)
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    # Fallback for local development
    BOT_TOKEN = "8618299910:AAF6UyVQ6n0gFbDar9XYPq4QCCKPhxqegaY"

# Get admin IDs from environment
ADMIN_IDS = []
admin_ids_str = os.getenv('ADMIN_IDS', '')
if admin_ids_str:
    ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(',')]
else:
    # Fallback for local development
    ADMIN_IDS = [5468237078]  # Replace with your user ID

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
BOTS_DIR = os.path.join(BASE_DIR, "bots")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Create directories
for dir_path in [UPLOAD_DIR, BOTS_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_EXTENSIONS = ['.py', '.zip']
