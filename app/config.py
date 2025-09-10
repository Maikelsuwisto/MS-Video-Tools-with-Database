import os

# Railway provides DATABASE_URL directly
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:wnjQUAGFTDbmvCDHEUkJtUGfuCYbTTxU@shinkansen.proxy.rlwy.net:18315/railway?sslmode=require")


JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", 60))
