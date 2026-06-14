# app.py
# Complete Flask app with registration, login, and private notes (CRUD).
# Comments below explain every step for a beginner.

from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import os
from werkzeug.utils import secure_filename
# --------------------
# App Initialization
# --------------------
app = Flask(__name__)
app.secret_key = "myverysecretkey"  # change this in production

# Configure upload folder
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    conn = sqlite3.connect('notesdb.sqlite')
    conn.row_factory = sqlite3.Row
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
        
        # Hash the password before saving
        hashed_pw = generate_password_hash(password)
  
        conn = get_db_connection()
        cur = conn.cursor()
      
        # Check if username already exists
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        exists = cur.fetchone()
        
        if exists:
            # Close connection and inform user
            cur.close()
            conn.close()
            flash("Username already taken. Choose another.", "danger")
            return redirect('/register')
      
        # Insert new user into users table
        cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, hashed_pw))
        conn.commit()
        cur.close()
        conn.close()

        # Send registration confirmation email
        msg = Message('Registration Confirmation', recipients=[email])
        msg.body = f"Hello {username},\n\nYou have successfully registered for the Notes App. Welcome!\n\nBest regards,\nNotes App Team"

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

        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()

        cur.close()
        conn.close()
 
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email']    = user[2]
            session['profile_pic'] = user[4] if user[4] else None  # profile_pic is column index 4
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
            "UPDATE users SET password=? WHERE username=?",
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
        cur.execute("INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)",
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
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    sort = request.args.get('sort', 'newest')  # default newest
    order = "DESC" if sort == 'newest' else "ASC"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT id, title, content, created_at, is_pinned
        FROM notes WHERE user_id = ?
        ORDER BY is_pinned DESC, created_at {order}
    """, (user_id,))
    rows = cur.fetchall()

    notes = []
    for row in rows:
        notes.append({
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "created_at": row[3],
            "is_pinned": row[4]
        })
    cur.close()
    conn.close()
    return render_template('viewnotes.html', notes=notes, sort=sort)

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
    cur.execute("""SELECT id, title, content, created_at, is_pinned
                   FROM notes WHERE id = ? AND user_id = ?""",
                (note_id, user_id))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        flash("You don't have access to this note.", "danger")
        return redirect('/viewall')

    note = {"id": row[0], "title": row[1], "content": row[2],
            "created_at": row[3], "is_pinned": row[4]}
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
    cur.execute("SELECT id, title, content FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
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
        cur.execute("UPDATE notes SET title = ?, content = ? WHERE id = ? AND user_id = ?",
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
    cur.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
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
        WHERE user_id = ? 
        AND (title LIKE ? OR content LIKE ?)
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


# ------ filename -----
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('profile.html')

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form['email'].strip()
        user_id  = session['user_id']
        file     = request.files.get('profile_pic')

        conn = get_db_connection()
        cur  = conn.cursor()

        # Handle image upload
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"user_{user_id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute("UPDATE users SET username=?, email=?, profile_pic=? WHERE id=?",
                        (username, email, filename, user_id))
            session['profile_pic'] = filename
        else:
            cur.execute("UPDATE users SET username=?, email=? WHERE id=?",
                        (username, email, user_id))

        conn.commit()
        cur.close()
        conn.close()

        # Update session so navbar refreshes instantly
        session['username'] = username
        session['email']    = email

        flash("Profile updated successfully!", "success")
        return redirect('/profile')

    return render_template('edit_profile.html')    


# Pin/Unpin Note (UPDATE is_pinned) - restricted
@app.route('/pinnote/<int:note_id>', methods=['POST'])
def pinnote(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    # Check current pin status
    cur.execute("SELECT is_pinned FROM notes WHERE id = ? AND user_id = ?",
                (note_id, user_id))
    row = cur.fetchone()

    if row:
        new_status = 0 if row[0] == 1 else 1  # toggle
        cur.execute("UPDATE notes SET is_pinned = ? WHERE id = ? AND user_id = ?",
                    (new_status, note_id, user_id))
        conn.commit()
        flash("Note pinned! 📌" if new_status == 1 else "Note unpinned.", "success")

    cur.close()
    conn.close()
    return redirect('/viewall')


# --------------------
# Run App
# --------------------
if __name__ == '__main__':
    # debug=True for development only
    app.run(debug=True)