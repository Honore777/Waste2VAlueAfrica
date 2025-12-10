from extensions import db
from models import *
from sqlalchemy import create_engine

# PostgreSQL connection
pg_engine = create_engine("postgresql://eco_user:eco_password@localhost:5432/eco_chain_db")

# Create all tables
db.metadata.create_all(bind=pg_engine)

print("All tables created in PostgreSQL!")
