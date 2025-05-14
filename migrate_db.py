from app import app, db
from models import User, Game
import sqlite3
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        # Get connection to the database
        conn = db.engine.connect()
        
        # Check existing columns in users table
        try:
            # Add missing columns to users table if they don't exist
            conn.execute(text("ALTER TABLE users ADD COLUMN total_games INTEGER DEFAULT 0"))
            print("Added total_games column")
        except:
            print("total_games column already exists or error adding it")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN wins INTEGER DEFAULT 0"))
            print("Added wins column")
        except:
            print("wins column already exists or error adding it")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN losses INTEGER DEFAULT 0"))
            print("Added losses column")
        except:
            print("losses column already exists or error adding it")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN draws INTEGER DEFAULT 0"))
            print("Added draws column")
        except:
            print("draws column already exists or error adding it")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN total_game_time INTEGER DEFAULT 0"))
            print("Added total_game_time column")
        except:
            print("total_game_time column already exists or error adding it")
        
        # Check if games table exists, if not create it
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_mode VARCHAR(20) NOT NULL,
            difficulty VARCHAR(10),
            result VARCHAR(10) NOT NULL,
            moves INTEGER DEFAULT 0,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            duration INTEGER,
            board_state TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """))
        print("Created games table if it didn't exist")
        
        # Commit the transaction
        db.session.commit()
        print("Migration completed successfully")

if __name__ == "__main__":
    migrate_database()
