import os
import time
import psycopg2
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# Helper function to get database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        port=os.environ['DB_PORT']
    )


# Initialize database table (with retry logic in case DB is still booting)
def init_db():
    retries = 5
    while retries > 0:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    text VARCHAR(255) NOT NULL
                )
            ''')
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully!")
            break
        except psycopg2.OperationalError:
            retries -= 1
            print("Waiting for database to be ready...")
            time.sleep(2)


# Serve the HTML UI
@app.route('/')
def index():
    return render_template('index.html')


# API to get messages
@app.route('/api/messages', methods=['GET'])
def get_messages():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, text FROM messages ORDER BY id DESC')
    messages = cur.fetchall()
    cur.close()
    conn.close()

    # Convert list of tuples to list of dictionaries
    return jsonify([{'id': msg[0], 'text': msg[1]} for msg in messages])


# API to add a message
@app.route('/api/messages', methods=['POST'])
def add_message():
    data = request.get_json()
    text = data.get('text')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO messages (text) VALUES (%s) RETURNING id, text', (text,))
    new_msg = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'id': new_msg[0], 'text': new_msg[1]})


if __name__ == '__main__':
    init_db()
    # Run the app on all available IPs so Docker can map the port
    app.run(host='0.0.0.0', port=5007)