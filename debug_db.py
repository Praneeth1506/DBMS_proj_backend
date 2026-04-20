from dotenv import load_dotenv
load_dotenv()

from app.database.db import get_db_connection, save_conversation

conn = get_db_connection()
cur = conn.cursor()

# 1. List tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

# 2. Check user/users table
user_table = None
if 'user' in tables:
    user_table = 'user'
elif 'users' in tables:
    user_table = 'users'

if user_table:
    cur.execute(f'SELECT * FROM public."{user_table}" LIMIT 5')
    rows = cur.fetchall()
    print(f"Rows in {user_table}:", rows)
    
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{user_table}' AND table_schema='public'")
    cols = [r[0] for r in cur.fetchall()]
    print(f"Columns: {cols}")
else:
    print("No user/users table found!")

# 3. Check conversation table columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='conversation' AND table_schema='public'")
conv_cols = [r[0] for r in cur.fetchall()]
print("Conversation columns:", conv_cols)

cur.close()
conn.close()

# 4. Try save_conversation directly
print("\nTesting save_conversation...")
try:
    iid = save_conversation(
        userid=1,
        personid=10,
        transcribed_text="debug test",
        summarized_text="debug summary",
        detected_emotion="Neutral",
        location="TestRoom"
    )
    print(f"SUCCESS: interaction_id={iid}")
except Exception as e:
    print(f"FAILED: {e}")
