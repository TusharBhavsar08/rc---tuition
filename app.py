from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "rc_secret_key"

# --- Database Function ---
def run_query(query, parameters=()):
    with sqlite3.connect('students_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        conn.commit()
        return cursor

# --- Tables Setup (Address add kiya gaya) ---
run_query('''CREATE TABLE IF NOT EXISTS students 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, class TEXT, address TEXT)''')
run_query('''CREATE TABLE IF NOT EXISTS fees_history 
             (trans_id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount TEXT, date TEXT, mode TEXT)''')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    data = run_query("SELECT * FROM students").fetchall()
    return render_template('index.html', students=data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == '1234':
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Student Management (Address field ke saath) ---
@app.route('/add_student', methods=['POST'])
def add_student():
    run_query("INSERT INTO students (name, phone, class, address) VALUES (?, ?, ?, ?)", 
              (request.form.get('name'), request.form.get('phone'), request.form.get('class'), request.form.get('address')))
    return redirect(url_for('index'))

@app.route('/update_student/<int:id>', methods=['POST'])
def update_student(id):
    run_query("UPDATE students SET name=?, phone=?, class=?, address=? WHERE id=?", 
              (request.form.get('name'), request.form.get('phone'), request.form.get('class'), request.form.get('address'), id))
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_student(id):
    run_query("DELETE FROM students WHERE id=?", (id,))
    return redirect(url_for('index'))

# --- Fees Management ---
@app.route('/fees/<int:id>')
def fees(id):
    student = run_query("SELECT * FROM students WHERE id=?", (id,)).fetchone()
    history = run_query("SELECT * FROM fees_history WHERE student_id=?", (id,)).fetchall()
    return render_template('fees.html', s=student, h=history)

@app.route('/add_fee/<int:id>', methods=['POST'])
def add_fee(id):
    date_today = datetime.now().strftime("%d-%m-%Y")
    run_query("INSERT INTO fees_history (student_id, amount, date, mode) VALUES (?, ?, ?, ?)", 
              (id, request.form.get('amount'), date_today, request.form.get('mode')))
    return redirect(url_for('fees', id=id))

@app.route('/receipt/<int:trans_id>')
def receipt(trans_id):
    payment = run_query("SELECT * FROM fees_history WHERE trans_id=?", (trans_id,)).fetchone()
    student = run_query("SELECT * FROM students WHERE id=?", (payment[1],)).fetchone()
    return render_template('receipt.html', student=student, payment=payment)

@app.route('/export')
def export_data():
    students = run_query("SELECT * FROM students").fetchall()
    if not os.path.exists("Records"): os.makedirs("Records")
    for s in students:
        path = os.path.join("Records", s[3])
        if not os.path.exists(path): os.makedirs(path)
        with open(os.path.join(path, f"{s[1]}.txt"), "w") as f:
            f.write(f"ID: {s[0]}\nName: {s[1]}\nPhone: {s[2]}\nClass: {s[3]}\nAddress: {s[4]}")
    return " Records Exported! <a href='/'>Back</a>"

if __name__ == '__main__':
    app.run(debug=True)