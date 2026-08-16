import os

BOT_TOKEN = "8630464736:AAFO-T_CDT63Z2ynycRHXQpop9alcX7vJk8"  # Replace with your bot token
ADMIN_IDS = [5468237078]  # Your Telegram user ID(s)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
BOTS_DIR = os.path.join(BASE_DIR, "bots")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Create directories if they don't exist
for dir_path in [UPLOAD_DIR, BOTS_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Supported file types
SUPPORTED_EXTENSIONS = ['.py', '.js', '.zip']
