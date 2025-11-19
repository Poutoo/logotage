
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
ERROR_WEBHOOK_URL = os.getenv("WEBHOOK_URL")
dev_id_str = os.getenv("DEVELOPER_ID")
DEVELOPER_ID = int(dev_id_str) if dev_id_str else 0

CHANNEL_IDS = [1440412689771004136, 1440412708854956083, 1440029744350363791, 1440007995936211004]

LOGO_PATH = "logo-magic.png"

if not TOKEN:
    raise ValueError("Le token Discord est introuvable ! Vérifiez votre fichier .env")