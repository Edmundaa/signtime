from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import models as dbHandler

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a real secret key

@app.route('/', methods=['GET', 'POST'])
def home():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		if dbHandler.validateUser(username, password):
			session['username'] = username
			return f'Welcome, {username}!'
		return render_template('index.html', error='Invalid credentials')
	return render_template('index.html')

@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		username = request.form['username']
		password = generate_password_hash(request.form['password'])
		if dbHandler.insertUser(username, password):
			return redirect(url_for('home'))
		return render_template('register.html', error='Username already exists')
	return render_template('register.html')

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')