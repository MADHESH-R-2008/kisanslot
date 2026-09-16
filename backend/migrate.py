import os
from sqlalchemy import create_engine, text

# Read the cloud database URL from the environment; never commit credentials.
DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE centres ADD COLUMN code VARCHAR(20) UNIQUE;"))
        conn.commit()
        print("Successfully added 'code' column to centres table.")
    except Exception as e:
        print(f"Error (column might already exist?): {e}")

    # Also make sure the seed script runs to populate it if they are empty?
    # Actually wait, maybe I can just update the code for the existing ones.
    conn.execute(text("UPDATE centres SET code = CONCAT('CTR', id) WHERE code IS NULL;"))
    conn.commit()
    print("Populated missing 'code' values.")
