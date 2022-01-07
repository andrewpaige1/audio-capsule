from flask import Flask, request, render_template, redirect, url_for, session
import cloudinary as Cloud
import cloudinary.uploader
from os import environ
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import backref
from datetime import datetime
import bcrypt


app = Flask(__name__)
app.secret_key = environ.get('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL').replace("://", "ql://", 1)
#"sqlite:///sqlite3.db"
#environ.get('DATABASE_URL').replace("://", "ql://", 1)
db = SQLAlchemy(app)

Cloud.config.update = ({
    'cloud_name':environ.get('CLOUDINARY_CLOUD_NAME'),
    'api_key': environ.get('CLOUDINARY_API_KEY'),
    'api_secret': environ.get('CLOUDINARY_API_SECRET')
})

user_file = db.Table("user_file", 
    db.Column('user_id', db.Integer, db.ForeignKey("user.id")),
    db.Column('file_id', db.Integer, db.ForeignKey("files.id"))
)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.now)
    username = db.Column(db.String(50))
    email = db.Column(db.String(300))
    password = db.Column(db.LargeBinary)
    uploads = db.relationship("Files", secondary=user_file, backref=db.backref("uploaded", lazy="dynamic"))
class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.now)
    url = db.Column(db.String(300))
    note = db.Column(db.String(300))


@app.route('/')
def index():
  if 'username' in session:
    return redirect(url_for('profile'))
  return redirect(url_for('register'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':#handle form
        existing_user = User.query.filter_by(username=request.form['username']).first()#find the first user that matches name
        if existing_user:#check if user exists
            #hash the password and compare it to the one stored in the db
            existing_pass = existing_user.password
            if bcrypt.checkpw(request.form['pass'].encode('utf-8'), existing_pass):
                #create session
                session['username'] = request.form['username']
                return redirect(url_for('index'))
            else:
                print('wrong username or password')
        else:
            print('wrong username or password')
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        #find existing user
        email = request.form['email']
        existing_user = User.query.filter_by(email=request.form['username']).first()
        #if there's no previous users let them sign up
        if existing_user is None:
            #hashed password
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            #creates a new user in table
            #i think its saying INSERT USER in USERS
            #tbh it's been a year since i looked at sql
            username = request.form['username']
            user = User(username=username, email=email, password=hashpass)
            #this prepares the user to be added to the table
            db.session.add(user)
            #commit new user to table
            db.session.commit()
            session['username'] = username
            print('user added')
            return redirect(url_for('index'))
        else:
            print('user exists')
    return render_template("register.html")

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/upload', methods=['POST'])
def upload():
  if 'username' in session:
    audio = request.files['audio']
    #name = request.form['username']
    if request.method == 'POST' and 'audio' not in request.files:
        return {'status': 'please submit a valid picture'}
    audio = cloudinary.uploader.upload(audio, resource_type = "video")
    print(audio['secure_url'])
    user = User.query.filter_by(username=session['username']).first()
    file = Files(url=audio['secure_url'], note=request.form['note'])
    user.uploads.append(file)
    db.session.add(file)
    db.session.commit()
    print("File uploaded succesfully")
    return redirect(url_for('index'))
  return redirect(url_for('register'))

@app.route('/profile')
def profile():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        uploads = user.uploads
        return render_template('profile.html', uploads=uploads)
    return redirect(url_for('register'))

if __name__ == '__main__':
  app.run(debug=True)