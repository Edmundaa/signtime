import logging
logging.basicConfig(level=logging.DEBUG)

from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
import sqlite3
import random
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Change the file extension to .db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Add a secret key for Flask-Login
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Allows configuration like settings to be tucked away in a separate file.  See config.py
app.config.from_object(Config)

# Add User model if not already present
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
def init_db():
    with app.app_context():
        try:
            db.create_all()
            logging.debug("Database tables created successfully")
        except Exception as e:
            logging.error(f"Error creating database tables: {str(e)}")

# Call init_db() function
init_db()

# The home page
@app.route('/')
def home():
  return render_template('index.html')


# Displays all teddys in the database
# TODO: link each teddy to its own details page
@app.route('/dictionary')
def all_definitions():
    if not current_user.is_authenticated:
        return render_template("dictionary_login_required.html")
    
    conn = sqlite3.connect(app.config['DATABASE'])
    cur = conn.cursor()
    cur.execute("SELECT * FROM Definitions ORDER BY name;")
    definitions = cur.fetchall()
    conn.close()
    return render_template("dictionary.html", definitions=definitions)


# Individual teddy details page.
@app.route('/teddy/<int:id>')
def teddy_details(id):
  # print("The teddy id is {}".format(id))  # DEBUG
  conn = sqlite3.connect(app.config['DATABASE'])
  cur = conn.cursor()
  
  # You might be asking yourself why you couldn't write a query like: cur.execute(f"SELECT * FROM Teddy WHERE id={id};") 
  # Simply put, this is insecure and allows for SQL injection.  For example, if someone set variable id="2; DROP TABLE *;" then the table gets deleted.
  # Instead, it's better to use the id=? and to provide the parameter as a separate tuple.  "(id,)" looks weird but it's simply a tuple (collection) with one value.
  cur.execute("SELECT * FROM Teddy WHERE id=?;",(id,))
  # fetchone returns a tuple containing the data for one entry
  teddy = cur.fetchone()
  conn.close()
  return render_template("teddy.html", teddy=teddy)


# about Teddy Bears Picnic
@app.route('/about')
def about():
  formstuff = None
  if len(request.args) > 0:
    formstuff = []
    formstuff.append(request.args.get('username'))
    formstuff.append(request.args.get('password'))
  return render_template('index.html', formstuff=formstuff)


# SignAi route
@app.route('/SignAi')
def sign_ai():
    return render_template('SignAi.html')


# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('home'))

# Terms and Conditions route
@app.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

if __name__ == '__main__':
  app.run(debug=app.config['DEBUG'], port=8080, host='0.0.0.0') 