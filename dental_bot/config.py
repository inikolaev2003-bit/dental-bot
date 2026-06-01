import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8404661720:AAE6FKyux6DlOoysgSVLuv5VZdtqLrUmzj4")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456")
ADMIN_COMMAND = "/admin"