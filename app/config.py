import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DatabaseConfig:
    # AIVEN Database Configuration
    DB_HOST = os.getenv("DB_HOST", "mysql-1584479f-nugasteros13-34d8.c.aivencloud.com")
    DB_PORT = os.getenv("DB_PORT", "13582")
    DB_USER = os.getenv("DB_USER", "avnadmin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "YOUR_PASSWORD")
    DB_NAME = os.getenv("DB_NAME", "coworking")
    
    @property
    def database_url(self):
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

