from flask import Flask, render_template,redirect,url_for,request,redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'yogendrachaurasiya30@gmail.com'
app.config['MAIL_PASSWORD'] = 'rwmvymykfioubkig'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

db = SQLAlchemy(app)
mail = Mail(app)

# Generate OTP
def generate_otp():
    otp = ""
    for _ in range(6):
        otp += str(random.randint(0, 9))
    return otp

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    semester = db.Column(db.Integer, nullable=False)
    student_id = db.Column(db.String(20), nullable=False, unique=True)

@app.route('/')
def user_index():
    return redirect(url_for('userLogin'))

@app.route('/userLogin', methods=['GET', 'POST'])
def userLogin():
    if request.method == 'POST':
        email = request.form['email']
        user = Student.query.filter_by(email=email).first()
        if user:
            otp = generate_otp()
            session['otp'] = otp
            session['email'] = email
            send_otp_email(email, otp)
            return redirect(url_for('verify_otp'))
        else:
            flash('User not found. Please enter the email with which you registered.', 'error')
           
    return render_template('userLogin.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'otp' in session and 'email' in session:
        if request.method == 'POST':
            otp_entered = request.form['otp']
            if otp_entered == session['otp']:
                session.pop('otp', None)
                session.pop('email', None)
                return redirect(url_for('index'))
            else:
                flash('Invalid OTP. Please try again.', 'error')
                return redirect(url_for('verify_otp'))
        return render_template('verify_otp.html')
    else:
        return redirect(url_for('userLogin'))

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    msg = Message('OTP Verification', sender='yogendrachaurasiya30@example.com', recipients=[email])
    msg.body = f'Your OTP for login is: {otp}'
    mail.send(msg)

@app.route('/userRegister', methods=['GET', 'POST'])
def userRegister():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        semester = request.form['semester']
        student_id = request.form['student_id']

        # Check if the email or student_id already exists
        existing_email = Student.query.filter_by(email=email).first()
        existing_student_id = Student.query.filter_by(student_id=student_id).first()

        if existing_email:
            flash('User with this email already exists. Please use a different email.', 'error')
        elif existing_student_id:
            flash('User with this student ID already exists. Please use a different student ID.', 'error')
        else:
            # If neither email nor student_id exists, proceed with registration
            new_student = Student(name=name, email=email, semester=semester, student_id=student_id)
            db.session.add(new_student)
            db.session.commit()
            return redirect(url_for('userLogin'))

    return render_template('userRegister.html')



class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@app.route('/admin')
def admin():
    # Check if admin is logged in
    if 'admin_id' in session:
        # Get the current admin from the database
        admin_id = session['admin_id']
        current_admin = Admin.query.get(admin_id)
        # Render the admin dashboard template with the current_admin variable
        return render_template('admin.html', current_admin=current_admin)
    else:
        # If admin is not logged in, redirect to the login page
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Initialize error message
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query the database for the admin with the provided username
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.password == password:
            # Set the admin's ID in the session
            session['admin_id'] = admin.id
            # Redirect the admin to the dashboard
            return redirect(url_for('admin'))
        else:
            # Set error message based on reason for unsuccessful login
            if not admin:
                error = 'Username not found. Please try again.'
            else:
                error = 'Incorrect password. Please try again.'

    # Render the login page with the error message
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None  # Initialize error message
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username is already taken
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            error = 'Username already exists. Please choose a different one.'
        else:
            # Create a new admin
            new_admin = Admin(username=username, password=password)
            db.session.add(new_admin)
            db.session.commit()
            # Redirect to the login page on successful registration
            return redirect(url_for('login'))

    # Render the registration page with the error message
    return render_template('register.html', error=error)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST' or request.method == 'GET':
        # Clear the admin ID from the session
        session.pop('admin_id', None)
        # Render the logout success template
        return render_template('logout_success.html')

# Add a route for the logout success page
@app.route('/logout/success')
def logout_success():
    return render_template('logout_success.html')



class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)# Add 'name' attribute
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    ongoing = db.Column(db.Boolean, default=False)
    candidates = db.relationship('Candidate', backref='election', lazy=True)  

    def __init__(self, election_id, name):
        self.election_id = election_id
        self.name = name

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    votes = db.Column(db.Integer, default=0)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)


@app.route('/index')
def index():
    candidates = Candidate.query.all()
    return render_template('index.html', candidates=candidates)

# @app.route('/admin', methods=['GET', 'POST'])
# def admin():
#     if request.method == 'POST':
#         num_candidates = int(request.form['num_candidates'])
#         return render_template('add_candidates.html', num_candidates=num_candidates)
#     return render_template('admin.html')

@app.route('/view_elections')
def view_elections():
    elections = Election.query.all()
    return render_template('view_elections.html', elections=elections)

@app.route('/add_candidates/<int:election_id>/<int:num_candidates>', methods=['GET', 'POST'])
def add_candidates(election_id, num_candidates):
    if request.method == 'GET':
        return render_template('add_candidates.html', election_id=election_id, num_candidates=num_candidates)
    elif request.method == 'POST':
        with app.app_context():
            for i in range(num_candidates):
                candidate_name = request.form[f'candidate_name_{i}']
                candidate_description = request.form[f'candidate_description_{i}']
                candidate_image_url = request.form[f'candidate_image_url_{i}']
                candidate = Candidate(name=candidate_name, description=candidate_description, image_url=candidate_image_url, election_id=election_id)
                db.session.add(candidate)
            db.session.commit()
        return redirect(url_for('admin'))
    
    
@app.route('/create_election', methods=['GET', 'POST'])
def create_election():
    if request.method == 'POST':
        election_name = request.form['election_name']
        election_id = request.form['election_id']
        num_candidates = int(request.form['num_candidates'])

        try:
            # Create new election within the application context
            with app.app_context():
                new_election = Election(election_id=election_id, name=election_name)
                db.session.add(new_election)
                db.session.commit()
                # Reload the new election instance to ensure it's bound to the session
                db.session.refresh(new_election)
        except IntegrityError as e:
            # Rollback the session to prevent partial changes
            db.session.rollback()
            # Handle the IntegrityError by displaying a user-friendly message
            return "Failed to create election. An election with the same ID already exists."

        # If the election is created successfully, redirect to the page for adding candidates
        return redirect(url_for('add_candidates', election_id=new_election.id, num_candidates=num_candidates))

    # If the request method is GET, render the create new election form
    return render_template('create_election.html')

@app.route('/start_session/<int:election_id>')
def start_session(election_id):
    election = Election.query.get_or_404(election_id)
    if not election.ongoing:
        election.ongoing = True
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Voting session started'})
    else:
        return jsonify({'status': 'error', 'message': 'Voting session already ongoing'})

@app.route('/end_session/<int:election_id>')
def end_session(election_id):
    election = Election.query.get_or_404(election_id)
    if election.ongoing:
        election.ongoing = False
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Voting session ended'})
    else:
        return jsonify({'status': 'error', 'message': 'No ongoing voting session'})


@app.route('/view_candidates')
def view_candidates():
    candidates = Candidate.query.all()

    if not candidates:
        return render_template('no_candidates_found.html')  # Render a template for no candidates found

    return render_template('view_candidates.html', candidates=candidates)

@app.route('/update_candidate/<int:candidate_id>', methods=['GET', 'POST'])
def update_candidate(candidate_id):
    candidate = Candidate.query.get(candidate_id)
    if candidate:
        if request.method == 'GET':
            return render_template('update_candidate.html', candidate=candidate)
        elif request.method == 'POST':
            candidate.name = request.form['candidate_name']
            candidate.description = request.form['candidate_description']
            candidate.image_url = request.form['candidate_image_url']
            db.session.commit()
            return redirect(url_for('view_candidates'))
    else:
        return "Candidate not found"


@app.route('/delete_candidate/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    candidate = Candidate.query.get(candidate_id)
    if candidate:
        db.session.delete(candidate)
        db.session.commit()
    return redirect(url_for('view_candidates'))

        

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)