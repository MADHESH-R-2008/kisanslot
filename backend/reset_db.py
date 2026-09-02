import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from database import engine, Base
import models

with engine.begin() as conn:
    print("Dropping tables...")
    conn.execute(text("DROP TABLE IF EXISTS audit_logs;"))
    conn.execute(text("DROP TABLE IF EXISTS notifications;"))
    conn.execute(text("DROP TABLE IF EXISTS payments;"))
    conn.execute(text("DROP TABLE IF EXISTS procurement;"))
    conn.execute(text("DROP TABLE IF EXISTS bookings;"))
    conn.execute(text("DROP TABLE IF EXISTS slots;"))
    conn.execute(text("DROP TABLE IF EXISTS admins;"))
    conn.execute(text("DROP TABLE IF EXISTS centres;"))
    conn.execute(text("DROP TABLE IF EXISTS farmers;"))
    print("Tables dropped.")
    
print("Recreating tables...")
Base.metadata.create_all(bind=engine)
print("Tables recreated!")
