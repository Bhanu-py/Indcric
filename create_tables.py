"""
Script to create the missing SessionPlayer table in the database.
"""
import os
import django
from django.db import connection

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

def create_sessionplayer_table():
    """Create the SessionPlayer table manually."""
    with connection.cursor() as cursor:
        # Check if the table already exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename = 'cric_sessionplayer'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("Table cric_sessionplayer already exists.")
            return
        
        # Create the SessionPlayer table
        cursor.execute("""
        CREATE TABLE "cric_sessionplayer" (
            "id" bigserial NOT NULL PRIMARY KEY,
            "paid" boolean NOT NULL,
            "session_id" bigint NOT NULL,
            "team_id" bigint NOT NULL,
            "user_id" integer NOT NULL,
            CONSTRAINT "cric_sessionplayer_session_id_user_id_aa0b6474_uniq" UNIQUE ("session_id", "user_id"),
            CONSTRAINT "cric_sessionplayer_session_id_6b4d5c58_fk_cric_session_id" FOREIGN KEY ("session_id") REFERENCES "cric_session" ("id") DEFERRABLE INITIALLY DEFERRED,
            CONSTRAINT "cric_sessionplayer_team_id_71e35319_fk_cric_team_id" FOREIGN KEY ("team_id") REFERENCES "cric_team" ("id") DEFERRABLE INITIALLY DEFERRED,
            CONSTRAINT "cric_sessionplayer_user_id_be106d08_fk_cric_user_id" FOREIGN KEY ("user_id") REFERENCES "cric_user" ("id") DEFERRABLE INITIALLY DEFERRED
        );
        """)
        
        # Create indexes for the foreign keys
        cursor.execute("""
        CREATE INDEX "cric_sessionplayer_session_id_6b4d5c58" ON "cric_sessionplayer" ("session_id");
        """)
        cursor.execute("""
        CREATE INDEX "cric_sessionplayer_team_id_71e35319" ON "cric_sessionplayer" ("team_id");
        """)
        cursor.execute("""
        CREATE INDEX "cric_sessionplayer_user_id_be106d08" ON "cric_sessionplayer" ("user_id");
        """)
        
        print("Successfully created cric_sessionplayer table!")
        
        # Check if the attendance table exists first
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename = 'cric_attendance'
            );
        """)
        attendance_exists = cursor.fetchone()[0]
        
        if not attendance_exists:
            # Create the Attendance table if it doesn't exist
            cursor.execute("""
            CREATE TABLE "cric_attendance" (
                "id" bigserial NOT NULL PRIMARY KEY,
                "attended" boolean NOT NULL,
                "match_player_id" bigint NOT NULL,
                "payment_id" bigint NULL,
                CONSTRAINT "cric_attendance_match_player_id_key" UNIQUE ("match_player_id"),
                CONSTRAINT "cric_attendance_match_player_id_d3b3291e_fk" FOREIGN KEY ("match_player_id") REFERENCES "cric_sessionplayer" ("id") DEFERRABLE INITIALLY DEFERRED,
                CONSTRAINT "cric_attendance_payment_id_fk" FOREIGN KEY ("payment_id") REFERENCES "cric_payment" ("id") DEFERRABLE INITIALLY DEFERRED
            );
            """)
            
            cursor.execute("""
            CREATE INDEX "cric_attendance_match_player_id_d3b3291e" ON "cric_attendance" ("match_player_id");
            """)
            
            cursor.execute("""
            CREATE INDEX "cric_attendance_payment_id_idx" ON "cric_attendance" ("payment_id");
            """)
            
            print("Successfully created cric_attendance table!")
        else:
            # Check if match_player_id column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'cric_attendance'
                    AND column_name = 'match_player_id'
                );
            """)
            column_exists = cursor.fetchone()[0]
            
            if not column_exists:
                # Add match_player_id column
                cursor.execute("""
                ALTER TABLE "cric_attendance" 
                ADD COLUMN "match_player_id" bigint;
                """)
                
                cursor.execute("""
                ALTER TABLE "cric_attendance" 
                ADD CONSTRAINT "cric_attendance_match_player_id_d3b3291e_fk" 
                FOREIGN KEY ("match_player_id") REFERENCES "cric_sessionplayer" ("id") DEFERRABLE INITIALLY DEFERRED;
                """)
                
                cursor.execute("""
                CREATE INDEX "cric_attendance_match_player_id_d3b3291e" ON "cric_attendance" ("match_player_id");
                """)
                
                print("Successfully added match_player_id column to attendance table!")
            else:
                print("match_player_id column already exists in cric_attendance table.")

if __name__ == "__main__":
    create_sessionplayer_table()
