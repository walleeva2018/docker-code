from flask import Flask
import os 
import redis
import psycopg2

app = Flask(__name__)

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),  # Get hostname from environment
    port=6379,                                   # Default Redis port
    decode_responses=True                        # Get strings instead of bytes
)

def get_db():  
    # Read password from secret file (secure way)
    password_file = os.getenv("POSTGRES_PASSWORD_FILE")
    with open(password_file) as f:
        password = f.read().strip()
    

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),      # Hostname: 'db'
        database=os.getenv("POSTGRES_DB"),    # Database name: 'mydb'
        user=os.getenv("POSTGRES_USER"),      # Username: 'rafi'
        password=password                      # Password from file
    )
    return conn


def init_db():
    """Create visits table if it doesn't exist"""
    
    conn = get_db()
    cur = conn.cursor()
    
    # SQL: Create table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id SERIAL PRIMARY KEY,
            count INTEGER
        )
    """)
    
    conn.commit()     # Save changes
    cur.close()       # Close cursor
    conn.close()      # Close connection

init_db()

@app.route('/')
def home():
    """Homepage that tracks visits in both Redis and PostgreSQL"""
    
    # === Redis Counter ===
    # Increment and get the new value (atomic operation)
    redis_visits = r.incr("visits")
    
    # === PostgreSQL Counter ===
    conn = get_db()
    cur = conn.cursor()
    
    # Get the last count from database
    cur.execute("SELECT count FROM visits ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    
    # Calculate new count
    if row:
        pg_visits = row[0] + 1    # Increment last count
    else:
        pg_visits = 1              # First visit
    
    # Insert new count into database
    cur.execute("INSERT INTO visits(count) VALUES(%s)", (pg_visits,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    # Return HTML page
    return f"""
    <h1>🚀 Flask + Docker Compose</h1>
    <p>Redis visits: {redis_visits}</p>
    <p>Postgres visits: {pg_visits}</p>
    <p><small>Refresh to increment counters</small></p>
    """

port = int(os.environ.get("PORT", 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)