from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255), nullable=False)  # You were also missing password
    role = db.Column(db.String(20), nullable=False)       # ✅ Add this line
    email = db.Column(db.String(120))
    qualification = db.Column(db.String(120))
    projects = db.Column(db.Text)
    linkedin = db.Column(db.String(255))
    cgpa = db.Column(db.String(10))
    profile_image = db.Column(db.String(255))
    resume = db.Column(db.String(255))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.String(100))
    location = db.Column(db.String(100))
    company = db.Column(db.String(100))
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expiration_date = db.Column(db.Date, nullable=True)  # ✅ Already good

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    resume_filename = db.Column(db.String(200))  # filename of uploaded resume
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship('Job', backref='applications')
    seeker = db.relationship('User', backref='applications')

class SavedJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seeker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    seeker = db.relationship('User', backref='saved_jobs')
    job = db.relationship('Job', backref='saved_by')
