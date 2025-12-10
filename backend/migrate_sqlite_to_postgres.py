import sqlite3
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

# PostgreSQL connection
PG_URI = "postgresql://eco_user:eco_password@localhost:5432/eco_chain_db"
pg_engine = create_engine(PG_URI)
pg_metadata = MetaData()
pg_metadata.reflect(bind=pg_engine)

# SQLite connection
SQLITE_FILE = "eco_chain.db"
sqlite_conn = sqlite3.connect(SQLITE_FILE)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# SQLAlchemy session
Session = sessionmaker(bind=pg_engine)
session = Session()

tables = [
    "users",
    "categories",
    "listings",
    "listing_images",
    "tags",
    "posts",
    "post_tags",
    "post_upvotes",
    "comments",
    "conversations",
    "conversation_participants",
    "messages",
    "notifications",
    "wishlist"
]

def migrate_table(table_name):
    print(f"Migrating table: {table_name}")
    try:
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        if not rows:
            print(f"  No rows to migrate for {table_name}")
            return

        pg_table = Table(table_name, pg_metadata, autoload_with=pg_engine)

        # Convert sqlite row to dict for SQLAlchemy insert
        data = [dict(row) for row in rows]
        with pg_engine.begin() as conn:  # use 'begin()' for transaction
            conn.execute(pg_table.insert(), data)

        print(f"  Migrated {len(rows)} rows.")
    except Exception as e:
        print(f"  Error migrating {table_name}: {e}")

for table_name in tables:
    migrate_table(table_name)

sqlite_conn.close()
session.close()
print("Migration complete!")
