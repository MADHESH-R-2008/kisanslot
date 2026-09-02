import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from database import engine

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE admins ADD COLUMN role ENUM('FARMER','CENTRE_OPERATOR','ADMIN','SUPER_ADMIN') NOT NULL DEFAULT 'CENTRE_OPERATOR';"))
        print("Added role to admins")
    except Exception as e:
        print("Error adding role:", e)
    
    try:
        conn.execute(text("ALTER TABLE bookings MODIFY status ENUM('CONFIRMED','ARRIVED','VERIFIED','WAITING','CALLED','PROCESSING','COMPLETED','CANCELLED','NO_SHOW') NOT NULL DEFAULT 'CONFIRMED';"))
        print("Updated booking status ENUM")
    except Exception as e:
        print("Error updating booking status ENUM:", e)
