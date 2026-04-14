import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )
    return conn

def insert_conversation(userid, personid, text, location=None):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            INSERT INTO public.conversation (userid, personid, interactiondatetime, location, conversation, summarytext, emotiondetected)
            VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s)
            RETURNING interactionid;
        """
        # For now, summarytext and emotiondetected can be null or default
        cur.execute(query, (userid, personid, location, text, None, None))
        result = cur.fetchone()
        conn.commit()
        return result['interactionid'] if result else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
