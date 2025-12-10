from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    USER = os.getenv("USER")
    PASSWORD = os.getenv("PASSWORD")  # this should already be URL-encoded in .env
    HOST = os.getenv("HOST")
    PORT = os.getenv("PORT")
    DBNAME = os.getenv("DBNAME")
    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
