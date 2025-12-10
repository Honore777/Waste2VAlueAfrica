import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:aRSENEANTONIO%4077@db.qzpzupwxeawxrmpchqsb.supabase.co:5432/postgres?sslmode=require'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'supersecretkey'
