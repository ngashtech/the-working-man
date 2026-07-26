# database/models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
import json

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    worker_profile = db.relationship('WorkerProfile', backref='user', uselist=False)
    employer_profile = db.relationship('EmployerProfile', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_profile(self):
        if self.role == 'worker': return self.worker_profile
        elif self.role == 'employer': return self.employer_profile
        return None

class WorkerProfile(db.Model):
    __tablename__ = 'worker_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text)
    expected_pay_rate = db.Column(db.Float, nullable=False)
    pay_period = db.Column(db.String(10), default='hourly')
    availability_status = db.Column(db.String(20), default='available')
    id_document_path = db.Column(db.String(255))
    id_document_type = db.Column(db.String(50))
    id_number = db.Column(db.String(50))
    selfie_path = db.Column(db.String(255))
    id_verified = db.Column(db.Boolean, default=False)
    preferred_locations = db.Column(db.Text)
    rating_average = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    completed_jobs = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_locations_list(self):
        try: return json.loads(self.preferred_locations) if self.preferred_locations else []
        except: return []

class EmployerProfile(db.Model):
    __tablename__ = 'employer_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(100))
    address = db.Column(db.String(255))
    city = db.Column(db.String(50))
    verified_employer = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class JobPosting(db.Model):
    __tablename__ = 'job_postings'
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    service_type_needed = db.Column(db.String(50), nullable=False)
    location_name = db.Column(db.String(100), nullable=False)
    offered_pay_rate = db.Column(db.Float, nullable=False)
    pay_period = db.Column(db.String(10), default='hourly')
    is_active = db.Column(db.Boolean, default=True)
    is_filled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    employer = db.relationship('User', backref='jobs')

class Match(db.Model):
    __tablename__ = 'matches'
    id = db.Column(db.Integer, primary_key=True)
    job_posting_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    worker_profile_id = db.Column(db.Integer, db.ForeignKey('worker_profiles.id'), nullable=False)
    match_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='suggested')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    job = db.relationship('JobPosting', backref='matches')
    worker = db.relationship('WorkerProfile', backref='matches')

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    job_posting_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'))
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    worker_profile_id = db.Column(db.Integer, db.ForeignKey('worker_profiles.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)