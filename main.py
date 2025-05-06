from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime
import csv
from io import StringIO
from flask import Response
import base64
import os
import zipfile
from flask import send_file



app = Flask(__name__)
app.secret_key = 'tree-secret'
ADMIN_USERNAME = "admin"

# --- DB SETUP ---
def init_db():
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(BASE_DIR, 'tree', 'database.db')
    conn = sqlite3.connect(db_path)
    
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    email TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    tree_name TEXT,
                    tree_image BLOB,
                    q1 TEXT, q2 TEXT, q3 TEXT, q4 TEXT, q5 TEXT,
                    q6 TEXT, q7 TEXT, q8 TEXT, q9 TEXT, q10 TEXT,
                    q11 TEXT, q12 TEXT, q13 TEXT,
                    date TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pending_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    tree_name TEXT,
                    tree_image BLOB
          
                )''')

    conn.commit()
    conn.close()





# --- QUESTIONS ---
questions = [
    ("What color are the leaves?", ["Green", "Yellow", "Red", "Brown"]),
    ("Are there any Dying leaves?", ["many", "None", "Few", "don't know"]),
    ("Are there Fresh leaves?", ["many", "None", "Few", "don't know"]),
    ("Are there any mature leaves?", ["many", "None", "Few", "don't know"]),
    ("Are there any Open Flowers", ["many", "None", "Few", "don't know"]),
    ("Are there any new buds?", ["many", "None", "Few", "don't know"]),
    ("What is the moisture condition around the tree?", ["Wet", "Dry", "Muddy", "Normal"]),
    ("How is the sunlight exposure?", ["Full Sun", "Partial", "Shade", "Varies"]),
    ("Are there Unripe Fruits?", ["many", "None", "Few", "don't know"]),
    ("Are there Ripe Fruits?", ["many", "None", "Few", "don't know"]),
    ("Are there Open Fruits?", ["many", "None", "Few", "don't know"]),
    ("Any signs of animal activity?", ["Birds", "Insects", "worms", "None"]),
    ("Are there fallen fruits?", ["many", "None", "Few", "don't know"])
]


options = ["Option A", "Option B", "Option C", "Option D"]

# --- ROUTES ---
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def start():
    if 'user_id' not in session:
        return redirect('/login')

    tree_name = request.form['tree_name']
    image_file = request.files['tree_image']
    tree_image = image_file.read()

    conn = sqlite3.connect('tree/database.db')
    c = conn.cursor()
    c.execute('INSERT INTO pending_observations (user_id, tree_name, tree_image) VALUES (?, ?, ?)',
              (session['user_id'], tree_name, tree_image))
    observation_id = c.lastrowid  # get the ID of this entry
    conn.commit()
    conn.close()

    # Store only the ID in session — very small
    session['observation_id'] = observation_id
    return redirect('/observe')




@app.route('/observe', methods=['GET', 'POST'])
def observe():
    if 'user_id' not in session or 'observation_id' not in session:
        return redirect('/')

    observation_id = session['observation_id']
    conn = sqlite3.connect('tree/database.db')
    c = conn.cursor()
    c.execute('SELECT tree_name, tree_image FROM pending_observations WHERE id=?', (observation_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "Error: Observation not found."

    tree_name, tree_image = row

    if request.method == 'POST':
        answers = [request.form.get(f'q{i}') for i in range(1, 14)]
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect('tree/database.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO answers (
                user_id, tree_name, tree_image, q1, q2, q3, q4, q5,
                q6, q7, q8, q9, q10, q11, q12, q13, date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [session['user_id'], tree_name, tree_image] + answers + [date])
        conn.commit()
        conn.close()

        # Clean up temporary data
        session.pop('observation_id', None)
        return redirect('/success')

    return render_template('observe.html', questions=questions)

@app.route('/success')
def success():
    return render_template('success.html')







@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(BASE_DIR, 'tree', 'database.db')
        conn = sqlite3.connect(db_path)
        
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
            conn.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return 'Username already exists.'
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('tree/database.db')
        c = conn.cursor()
        c.execute('SELECT id, username FROM users WHERE username=? AND password=?', (username, password))
        user = c.fetchone()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]  # Store the username in session
            return redirect('/')
        else:
            return 'Invalid credentials.'
    return render_template('login.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        conn = sqlite3.connect('tree/database.db')
        c = conn.cursor()
        c.execute('SELECT username, password FROM users WHERE email=?', (email,))
        user = c.fetchone()
        if user:
            return f"Your username is '{user[0]}' and your password is '{user[1]}'."
        else:
            return 'Email not found.'
    return render_template('forgot.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect('/login')




@app.route('/submissions')
def submissions():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('tree/database.db')
    c = conn.cursor()

    # Get current user's username
    c.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    current_user = c.fetchone()[0]

    if current_user != ADMIN_USERNAME:
        conn.close()
        return "Access Denied: Admins only.", 403

    # Fetch all submission data including tree_image
    c.execute('''
        SELECT users.username, answers.tree_name, answers.tree_image,
               answers.q1, answers.q2, answers.q3, answers.q4, answers.q5,
               answers.q6, answers.q7, answers.q8, answers.q9, answers.q10, 
               answers.q11, answers.q12, answers.q13,
               answers.date
        FROM answers
        JOIN users ON answers.user_id = users.id
    ''')

    data = c.fetchall()
    conn.close()

    # Prepare the data for rendering
    processed_data = []
    for row in data:
        username = row[0]
        tree_name = row[1]
        tree_image_blob = row[2]
        image_base64 = base64.b64encode(tree_image_blob).decode('utf-8') if tree_image_blob else None
        answers = row[3:-1]
        date = row[-1]
        processed_data.append((username, tree_name, image_base64) + tuple(answers) + (date,))

    question_labels = [q[0] for q in questions]
    return render_template('submissions.html', submissions=processed_data, question_labels=question_labels)

@app.route('/export')
def export_submissions():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('tree/database.db')
    c = conn.cursor()

    # Confirm admin user
    c.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    current_user = c.fetchone()[0]
    if current_user != ADMIN_USERNAME:
        conn.close()
        return "Access Denied: Admins only.", 403

    # Fetch submission data (without image)
    c.execute('''
        SELECT users.username, answers.tree_name,
               answers.q1, answers.q2, answers.q3, answers.q4, answers.q5,
               answers.q6, answers.q7, answers.q8, answers.q9, answers.q10, answers.q11, answers.q12, answers.q13,
               answers.date
        FROM answers
        JOIN users ON answers.user_id = users.id
    ''')
    rows = c.fetchall()
    conn.close()

    # Write to CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Username", "Tree Name"] + [q[0] for q in questions] + ["Date"])
    writer.writerows(rows)

    # Return as downloadable response
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment; filename=submissions.csv"})


@app.route('/clear-submissions')
def clear_submissions():
    if 'user_id' not in session:
        return redirect('/login')

    # Allow only admin
    conn = sqlite3.connect('tree/database.db')
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    if c.fetchone()[0] != ADMIN_USERNAME:
        conn.close()
        return "Access Denied", 403

    # Clear answers
    c.execute('DELETE FROM answers')
    conn.commit()
    conn.close()
    return "✅ All submissions have been cleared."



if __name__ == '__main__':
    
    init_db()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

