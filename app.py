# app.py
# Complete Flask app with registration, login, and private notes (CRUD).
# Comments below explain every step for a beginner.

from flask import Flask, render_template, request, redirect, session, flash, url_for
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

# --------------------
# App Initialization
# --------------------
app = Flask(__name__)
app.secret_key = "myverysecretkey"  # change this in production

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'gantedi.srinidhi@gmail.com'
app.config['MAIL_PASSWORD'] = 'qzpc xkgn hfvw meyb'

mail = Mail(app)

# --------------------
# Database Connection Helper
# --------------------
def get_db_connection():
    """
    Create and return a new MySQL connection.
    Edit host/user/password/database if yours are different.
    """
    conn = pymysql.connect(
        host="localhost",
        user="root",       # change if your MySQL username is different
        password="root123",       # enter MySQL password if you have one
        database="notesdb" # the DB created from the SQL script above
    )
    return conn 

# --------------------
# Home (redirect)
# --------------------
@app.route('/')
def home():
    # If logged in -> show notes, else -> show login
    if 'user_id' in session:
        return redirect('/viewall')
    return redirect('/login')

@app.route('/about')
def about():
    return render_template('about.html')
# --------------------
# Register Route
# --------------------
@app.route('/register', methods=['GET','POST'])
def register():
    # If POST -> process registration form
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        print(username,email,password)

        # Basic checks (non-empty)
        if not username or not email or not password:
            flash("Please fill all fields.", "danger")
            return redirect('/register')
        print("Database connection established. hiiiiiiiiiiiiiiiiiiiiii")
        # Hash the password before saving
        hashed_pw = generate_password_hash(password)
        print("Database connection established. hwey")
        conn = get_db_connection()
        cur = conn.cursor()
        print("Database connection established.")
        # Check if username already exists
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        exists = cur.fetchone()
        print("Database connection established-1")
        if exists:
            # Close connection and inform user
            cur.close()
            conn.close()
            flash("Username already taken. Choose another.", "danger")
            return redirect('/register')
        print("Database connection established-2")
        # Insert new user into users table
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_pw))
        conn.commit()
        cur.close()
        conn.close()
        print("Database connection established-3")

        flash("Registration successful! You can now log in.", "success")
        return redirect('/login')

    # If GET -> show registration form
    return render_template('register.html')

# --------------------
# Login Route
# --------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If POST -> authenticate
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        # Basic check
        if not username or not password:
            flash("Please enter username and password.", "danger")
            return redirect('/login')

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash(f"Welcome, {user[1]}!", "success")
            return redirect('/viewall')
        else:
            flash("Invalid username or password.", "danger")
            return redirect('/login')
    # If GET -> show login page
    return render_template('login.html')

# --------------------
# Logout Route
# --------------------
@app.route('/logout')
def logout():
    # Clear session data
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')

@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        msg = Message(
            subject=f"Contact Form: {subject}",
            sender=app.config['MAIL_USERNAME'],
            recipients=[app.config['MAIL_USERNAME']]
        )

        msg.body = f"""
                        New Contact Form Submission

Name: {name}
Email: {email}

Message:
{message}
"""

        mail.send(msg)

        flash("Message sent successfully!", "success")
        return redirect('/contact')

    return render_template('contact.html')


# ----- FORGOT PASSWORD Route (UPDATE) -----

@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        hashed_pw = generate_password_hash(password)

        cur.execute(
            "UPDATE users SET password=%s WHERE username=%s",
            (hashed_pw, username)
        )

        conn.commit()

        cur.close()
        conn.close()

        flash("Password updated successfully.", "success")

        return redirect('/login')

    return render_template('forgotpassword.html')

# --------------------
# Add Note (CREATE)
# --------------------
@app.route('/addnote', methods=['GET', 'POST'])
def addnote():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        user_id = session['user_id']

        if not title or not content:
            flash("Title and content cannot be empty.", "danger")
            return redirect('/addnote')

        conn = get_db_connection()
        cur = conn.cursor()
        # Save note with user_id to keep notes private
        cur.execute("INSERT INTO notes (title, content, user_id) VALUES (%s, %s, %s)",
                    (title, content, user_id))
        conn.commit()
        cur.close()
        conn.close()

        flash("Note added successfully.", "success")
        return redirect('/viewall')

    # GET -> show add note form
    return render_template('addnote.html')

# --------------------
# View All Notes (READ ALL for logged-in user)
# --------------------
@app.route('/viewall')
def viewall():
    # Ensure user logged in
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, content, created_at FROM notes WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()

    notes = []
    for row in rows:
       notes.append({
        "id": row[0],
        "title": row[1],
        "content": row[2],
        "created_at": row[3]
    })
    cur.close()
    conn.close()

    return render_template('viewnotes.html', notes=notes)

# --------------------
# View Single Note (READ ONE) - restricted
# --------------------
@app.route('/viewnotes/<int:note_id>')
def viewnotes(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    # Select note only if it belongs to current user
    cur.execute("SELECT id, title, content, created_at FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
    row = cur.fetchone()

    if row:
        note = {
          "id": row[0],
          "title": row[1],
          "content": row[2],
          "created_at": row[3]
    }
    else:
        note = None
    cur.close()
    conn.close()

    if not note:
        # Either note doesn't exist or doesn't belong to the user
        flash("You don't have access to this note.", "danger")
        return redirect('/viewall')

    return render_template('singlenote.html', note=note)

# --------------------
# Update Note (UPDATE) - restricted
# --------------------
@app.route('/updatenote/<int:note_id>', methods=['GET', 'POST'])
def updatenote(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    # Check existence and ownership
    cur.execute("SELECT id, title, content FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
    row = cur.fetchone()

    if row:
        note = {
        "id": row[0],
        "title": row[1],
        "content": row[2]
    }
    else:
        note = None

    if not note:
        cur.close()
        conn.close()
        flash("You are not authorized to edit this note.", "danger")
        return redirect('/viewall')

    if request.method == 'POST':
        # Get updated data
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        if not title or not content:
            flash("Title and content cannot be empty.", "danger")
            return redirect(url_for('updatenote', note_id=note_id))

        # Update query guarded by user_id
        cur.execute("UPDATE notes SET title = %s, content = %s WHERE id = %s AND user_id = %s",
                    (title, content, note_id, user_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Note updated successfully.", "success")
        return redirect('/viewall')

    # If GET -> render update form with existing note data
    cur.close()
    conn.close()
    return render_template('updatenote.html', note=note)

# --------------------
# Delete Note (DELETE) - restricted
# --------------------
@app.route('/deletenote/<int:note_id>', methods=['POST'])
def deletenote(note_id):
    # This route expects a POST request (safer than GET for delete)
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    # Delete only if the note belongs to the current user
    cur.execute("DELETE FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
    flash("Note deleted.", "info")
    return redirect('/viewall')





# --------------------
# Search Notes 
# --------------------
@app.route('/search', methods=['POST'])
def search():
    if 'user_id' not in session:
        return redirect('/login')

    query = request.form['query'].strip()
    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, content, created_at 
        FROM notes 
        WHERE user_id = %s 
        AND (title LIKE %s OR content LIKE %s)
        ORDER BY created_at DESC
    """, (user_id, f"%{query}%", f"%{query}%"))

    rows = cur.fetchall()

    notes = []
    for row in rows:
        notes.append({
          "id": row[0],
          "title": row[1],
          "content": row[2],
          "created_at": row[3]
    })

    cur.close()
    conn.close()

    # reuse SAME page (better UX)
    return render_template('viewnotes.html', notes=notes, search_query=query)

# --------------------
# Run App
# --------------------
if __name__ == '__main__':
    # debug=True for development only
    app.run(debug=True)