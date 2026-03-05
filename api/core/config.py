"""App config (can merge with existing config later)"""

import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env')


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY","dev-secret-change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",60*24))