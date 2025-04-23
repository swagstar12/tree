from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'tree-secret'
ADMIN_USERNAME = "admin"

# --- DB SETUP ---
def init_db():
    conn = sqlite3.connect('database.db')
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
                    tree_id INTEGER,
                    q1 TEXT, q2 TEXT, q3 TEXT, q4 TEXT, q5 TEXT,
                    q6 TEXT, q7 TEXT, q8 TEXT, q9 TEXT, q10 TEXT
                )''')
    conn.commit()
    conn.close()

init_db()


tree_names_dict = {
    1: "Neem", 2: "Peepal", 3: "Banyan", 4: "Mango", 5: "Ashoka",
    6: "Gulmohar", 7: "Tamarind", 8: "Jackfruit", 9: "Eucalyptus", 10: "Indian Almond"
}

# --- QUESTIONS ---
questions = [
    ("What color are the leaves?", ["Green", "Yellow", "Red", "Brown"]),
    ("Are there any flowers visible?", ["Yes", "No", "Few", "Many"]),
    ("Is the tree shedding leaves?", ["Yes", "No", "Partially", "Cannot say"]),
    ("Do you see any insects?", ["Yes", "No", "Few", "Many"]),
    ("What is the moisture condition around the tree?", ["Wet", "Dry", "Muddy", "Normal"]),
    ("How is the sunlight exposure?", ["Full Sun", "Partial", "Shade", "Varies"]),
    ("Is the tree trunk healthy?", ["Yes", "No", "Some damage", "Cannot say"]),
    ("Any signs of animal activity?", ["Birds", "Insects", "Squirrels", "None"]),
    ("Are there any new buds?", ["Yes", "No", "Few", "Not sure"]),
    ("Are there fallen fruits?", ["Yes", "No", "Some", "Many"])
]


options = ["Option A", "Option B", "Option C", "Option D"]

# --- ROUTES ---
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    tree_names = ["Neem", "Peepal", "Banyan", "Mango", "Ashoka", "Gulmohar", "Tamarind", "Jackfruit", "Eucalyptus", "Indian Almond"]
    return render_template('index.html', trees=enumerate(tree_names, start=1))




@app.route('/tree/<int:tree_id>', methods=['GET', 'POST'])
def tree(tree_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        answers = [request.form.get(f'q{i}') for i in range(1, 11)]
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # ⏱️ Get current date and time
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO answers (user_id, tree_id, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [session['user_id'], tree_id] + answers + [date])
        
        conn.commit()
        conn.close()
        return redirect('/')
    
    return render_template('tree.html', tree_id=tree_id, questions=questions)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        conn = sqlite3.connect('database.db')
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
        conn = sqlite3.connect('database.db')
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
        conn = sqlite3.connect('database.db')
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
    
    # Fetch the username of the logged-in user
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    current_user = c.fetchone()[0]
    conn.close()

    # Only allow admin to view
    if current_user != ADMIN_USERNAME:
        return "Access Denied: Admins only.", 403
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        SELECT users.username, answers.tree_id, answers.q1, answers.q2, answers.q3, answers.q4, answers.q5,
               answers.q6, answers.q7, answers.q8, answers.q9, answers.q10, answers.date
        FROM answers
        JOIN users ON answers.user_id = users.id
    ''')
    data = c.fetchall()
    conn.close()

    # Replace tree_id with tree name
    processed_data = []
    for row in data:
        username = row[0]
        tree_id = row[1]
        tree_name = tree_names_dict.get(tree_id, f"Tree {tree_id}")
        answers = row[2:]
        date = row[-1]
        processed_data.append((username, tree_name) + tuple(answers) + (date,))

    question_labels = [q[0] for q in questions]
    return render_template('submissions.html', submissions=processed_data, question_labels=question_labels)





if __name__ == '__main__':
    app.run(debug=True)
