from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask import send_from_directory
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from functools import wraps
import mysql.connector
import os 
from werkzeug.utils import secure_filename
from datetime import timedelta


app = Flask(__name__)

app.permanent_session_lifetime = timedelta(minutes=30)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

bcrypt = Bcrypt(app)
UPLOAD_FOLDER = 'static/images/projects' 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY") # Set a secret key for session management

csrf = CSRFProtect(app)

def admin_required(func):
    @wraps(func)
    def decorated_functions(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("please login first.", "error")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return decorated_functions


db = mysql.connector.connect( 
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/skills')
def skills():
    return render_template("skills.html")

@app.route('/projects')
def projects():
    cursor =db.cursor()
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    cursor.close()

    return render_template('projects.html', projects=projects)  

@app.route('/services')
def services():
    return render_template("services.html")

@app.route('/admin')
@admin_required
def admin():
    cursor = db.cursor()
    query = """SELECT id, name, email, message, created_at FROM contacts ORDER BY id DESC"""
    cursor.execute(query)
    contacts = cursor.fetchall()
    cursor.close()
    return render_template('admin.html', contacts=contacts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple authentication (replace with actual authentication logic)
        stored_hash = os.getenv("ADMIN_PASSWORD_HASH")
    
        if (
            username == os.getenv("ADMIN_USERNAME")
            and bcrypt.check_password_hash(stored_hash, password)
        ):
            session.permanent = True
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            flash('Invalid credentials', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    print("logout route called")
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect('/login')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    print("Route reached")
    
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        cursor = db.cursor()
        query = """INSERT INTO contacts(name, email, message) VALUES(%s, %s, %s)"""
        values = (name, email, message)

        cursor.execute(query, values)

        db.commit()
        cursor.close()

        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect('/contact')
    return render_template('contact.html')

@app.route('/add-project', methods=['GET', 'POST'])
@admin_required
def add_project():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        github = request.form['github']
        image = request.files['image']

        filename =''
        if image: filename = secure_filename(image.filename)

        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


        cursor = db.cursor()

        query = """INSERT INTO projects(title, description, github_link, image) VALUES (%s, %s, %s, %s)""" 
        values = (title, description, github, filename)
        cursor.execute(query,values)

        db.commit()
        cursor.close()

        flash('Project added Successfully!', 'success')
        return redirect('/add-project')
    return render_template('add_project.html')

@app.route('/edit-project/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_project(id):
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        github = request.form['github']
       
        query = """UPDATE projects SET title=%s, description=%s, github_link=%s WHERE id=%s""" 
        values = (title, description, github, id)
        cursor.execute(query,values)

        db.commit()
   
        flash('Project updated Successfully!', 'success')
        return redirect('/manage-projects')

    cursor.execute("SELECT * FROM projects WHERE id=%s",(id,))
    project = cursor.fetchone()
    cursor.close()

    return render_template('edit_project.html', project=project)
    
@app.route('/delete-project/<int:id>')
@admin_required
def delete_project(id):
        cursor = db.cursor()

        cursor.execute("DELETE FROM projects WHERE id=%s", (id,))
        
        db.commit()
        cursor.close()

        flash('Project deleted Successfully!', 'success')
        return redirect('/admin')
    
@app.route('/manage-projects')
@admin_required
def manage_projects():
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM projects ORDER BY id DESC")

        projects = cursor.fetchall()
        cursor.close()
        return render_template('manage_projects.html', projects=projects)

@app.route('/download-resume')
def download_resume():
    return send_from_directory('resume', 'resume.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5001)

    
