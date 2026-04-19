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
        password=os.getenv("DB_PASSWORD", ""),
        sslmode=os.getenv("DB_SSLMODE", "prefer"),
    )
    return conn

import json

def save_conversation(userid, personid, transcribed_text, summarized_text, detected_emotion, location='Living Room'):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            INSERT INTO public.conversation (
                userid, personid, interactiondatetime, location, 
                conversation, summarytext, emotiondetected
            )
            VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s)
            RETURNING interactionid;
        """
        cur.execute(query, (userid, personid, location, transcribed_text, summarized_text, detected_emotion))
        result = cur.fetchone()
        conn.commit()
        return result['interactionid'] if result else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def save_person(name, relationship_type, prioritylevel=3, notes=''):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            INSERT INTO public.knownperson (name, relationshiptype, prioritylevel, notes)
            VALUES (%s, %s, %s, %s)
            RETURNING personid;
        """
        cur.execute(query, (name, relationship_type, prioritylevel, notes))
        result = cur.fetchone()
        conn.commit()
        return result['personid'] if result else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def save_faceencoding(personid, embedding_vector, confidencescore=1.0):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = """
            INSERT INTO public.faceencoding (personid, encodingdata, confidencescore)
            VALUES (%s, %s, %s)
            RETURNING faceencodingid;
        """
        cur.execute(query, (personid, json.dumps(embedding_vector), confidencescore))
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def save_userknownperson(userid, personid):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = """
            INSERT INTO public.userknownperson (userid, personid)
            VALUES (%s, %s);
        """
        cur.execute(query, (userid, personid))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
