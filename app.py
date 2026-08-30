# app.py - The Working Man Platform (Refined & Production-Ready)
import sys
import os
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()

from config import config_by_name
from database.models import (
    db, bcrypt, User, WorkerProfile, EmployerProfile,
    JobPosting, Match, Review, Message, Notification, AdminLog
)

# ----------------------------------------------------------------------
# App factory and configuration
# ----------------------------------------------------------------------
app = Flask(__name__)

config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config_by_name.get(config_name, config_by_name['development']))

# Ensure upload directories exist
upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
os.makedirs(upload_folder, exist_ok=True)
os.makedirs(os.path.join(upload_folder, 'documents'), exist_ok=True)
os.makedirs(os.path.join(upload_folder, 'selfies'), exist_ok=True)

# Initialise extensions
db.init_app(app)
bcrypt.init_app(app)

# Initialise login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))   # SQLAlchemy 2.0 style

# ----------------------------------------------------------------------
# Helper functions and decorators
# ----------------------------------------------------------------------
def allowed_file(filename):
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def worker_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'worker':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorator

def employer_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'employer':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorator

def admin_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorator

def _time_ago(dt):
    if not dt:
        return 'Unknown'
    diff = datetime.utcnow() - dt
    if diff.days > 30:
        return f"{diff.days // 30}mo ago"
    if diff.days > 0:
        return f"{diff.days}d ago"
    if diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    return 'Just now'

# ----------------------------------------------------------------------
# Database initialisation and admin auto-creation
# ----------------------------------------------------------------------
with app.app_context():
    db.create_all()
    print("✅ Database ready")

    # Create default admin if it doesn't exist
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@workingman.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'Admin@123')
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            email=admin_email,
            phone='+254700000000',
            full_name='System Admin',
            role='admin',
            is_verified=True,
            is_active=True
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin created: {admin_email}")

# ----------------------------------------------------------------------
# Context processor for global template variables
# ----------------------------------------------------------------------
@app.context_processor
def inject_globals():
    unread_notifications = 0
    unread_messages = 0
    if current_user.is_authenticated:
        try:
            unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            unread_messages = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
        except Exception:
            pass
    return {
        'now': datetime.utcnow(),
        'unread_notifications': unread_notifications,
        'unread_messages': unread_messages,
    }

# ----------------------------------------------------------------------
# Main routes
# ----------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/help-center')
def help_center():
    return render_template('help_center.html')

@app.route('/safety-tips')
def safety_tips():
    return render_template('safety_tips.html')

@app.route('/success-stories')
def success_stories():
    return render_template('success_stories.html')

# ----------------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({
            'success': True,
            'user': {'id': current_user.id, 'full_name': current_user.full_name, 'role': current_user.role}
        })

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=bool(request.form.get('remember')))
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f'Welcome back, {user.full_name}!', 'success')
            return jsonify({
                'success': True,
                'user': {'id': user.id, 'full_name': user.full_name, 'role': user.role}
            })

        flash('Invalid email or password.', 'error')
        return jsonify({'success': False, 'message': 'Invalid email or password'})

    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if User.query.filter_by(email=email).first():
            flash('Password reset instructions sent.', 'success')
        else:
            flash('No account found.', 'error')
        return redirect(url_for('login'))
    return render_template('auth/forgot_password.html')

# ----------------------------------------------------------------------
# Dashboard (role-based redirect)
# ----------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'worker':
        return redirect(url_for('worker_dashboard'))
    elif current_user.role == 'employer':
        return redirect(url_for('employer_dashboard'))
    elif current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index'))

# ----------------------------------------------------------------------
# Worker routes
# ----------------------------------------------------------------------
@app.route('/register/worker', methods=['GET', 'POST'])
def register_worker():
    if current_user.is_authenticated:
        return redirect(url_for('worker_dashboard'))

    if request.method == 'POST':
        data = request.form
        errors = []

        if not data.get('full_name', '').strip() or len(data.get('full_name', '').strip()) < 3:
            errors.append('Full name is required (minimum 3 characters).')
        if not data.get('email') or '@' not in data.get('email', ''):
            errors.append('A valid email address is required.')
        if User.query.filter_by(email=data.get('email', '').strip().lower()).first():
            errors.append('Email is already registered.')
        if not data.get('phone', '').strip():
            errors.append('Phone number is required.')
        if not data.get('password') or len(data.get('password', '')) < 8:
            errors.append('Password must be at least 8 characters.')
        if data.get('password') != data.get('confirm_password', ''):
            errors.append('Passwords do not match.')
        if not data.get('service_type'):
            errors.append('Service type is required.')
        if not data.get('country'):
            errors.append('Country is required.')
        if not data.get('county'):
            errors.append('County/region is required.')
        if not data.getlist('preferred_locations'):
            errors.append('Select at least one work location.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('worker/register.html')

        try:
            user = User(
                email=data.get('email', '').strip().lower(),
                phone=data.get('phone', '').strip(),
                full_name=data.get('full_name', '').strip(),
                role='worker'
            )
            user.set_password(data.get('password', ''))
            db.session.add(user)
            db.session.flush()

            try:
                exp_years = int(data.get('experience_years', 0))
                pay_rate = float(data.get('expected_pay_rate', 0))
            except (ValueError, TypeError):
                exp_years = 0
                pay_rate = 0

            profile = WorkerProfile(
                user_id=user.id,
                service_type=data.get('service_type'),
                experience_years=exp_years,
                bio=data.get('bio', '').strip() or None,
                expected_pay_rate=pay_rate,
                pay_period=data.get('pay_period', 'hourly'),
                availability_status='available',
                preferred_locations=json.dumps(data.getlist('preferred_locations')),
                country=data.get('country', 'Kenya'),
                county=data.get('county'),
                city=data.get('city', '').strip() or None
            )
            db.session.add(profile)
            db.session.commit()

            login_user(user)
            flash(f'Registration successful! Welcome, {user.full_name}.', 'success')
            return redirect(url_for('worker_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')

    return render_template('worker/register.html')

@app.route('/worker/dashboard')
@login_required
@worker_required
def worker_dashboard():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('register_worker'))

    completed_jobs = Match.query.filter_by(worker_profile_id=profile.id, status='completed').count()
    pending_applications = Match.query.filter_by(worker_profile_id=profile.id, status='applied').count()
    active_matches = Match.query.filter(
        Match.worker_profile_id == profile.id,
        Match.status.in_(['contacted', 'interviewed', 'hired'])
    ).count()

    recent_matches = Match.query.filter_by(worker_profile_id=profile.id) \
        .order_by(Match.updated_at.desc()).limit(10).all()

    # Only show jobs from the worker's country (and ideally same county)
    available_jobs = JobPosting.query.filter_by(
        service_type_needed=profile.service_type,
        is_active=True,
        is_filled=False,
        country=profile.country
    ).order_by(JobPosting.created_at.desc()).limit(10).all()

    return render_template(
        'worker/dashboard.html',
        worker=profile,
        user=current_user,
        completed_jobs=completed_jobs,
        pending_matches=pending_applications,
        active_matches=active_matches,
        recent_matches=recent_matches,
        available_jobs=available_jobs
    )

@app.route('/worker/profile')
@login_required
@worker_required
def worker_profile():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('worker_dashboard'))
    reviews = Review.query.filter_by(worker_profile_id=profile.id) \
        .order_by(Review.created_at.desc()).limit(10).all()
    return render_template('worker/profile.html', worker=profile, user=current_user, reviews=reviews)

@app.route('/worker/profile/create')
@login_required
@worker_required
def create_worker_profile_full():
    return render_template('worker/create_profile.html', user=current_user)

@app.route('/worker/profile/edit', methods=['GET', 'POST'])
@login_required
@worker_required
def edit_worker_profile():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('worker_dashboard'))

    if request.method == 'POST':
        try:
            profile.service_type = request.form.get('service_type', profile.service_type)
            profile.experience_years = int(request.form.get('experience_years', profile.experience_years))
            profile.bio = request.form.get('bio', profile.bio)
            profile.expected_pay_rate = float(request.form.get('expected_pay_rate', profile.expected_pay_rate))
            profile.pay_period = request.form.get('pay_period', profile.pay_period)
            profile.availability_status = request.form.get('availability_status', profile.availability_status)

            # Optional country/county update
            if request.form.get('country'):
                profile.country = request.form.get('country')
            if request.form.get('county'):
                profile.county = request.form.get('county')
            if request.form.get('city'):
                profile.city = request.form.get('city')

            locations = request.form.getlist('preferred_locations')
            if locations:
                profile.preferred_locations = json.dumps(locations)

            if 'selfie' in request.files:
                file = request.files['selfie']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{current_user.id}_selfie_{file.filename}")
                    path = os.path.join(app.config['UPLOAD_FOLDER'], 'selfies')
                    os.makedirs(path, exist_ok=True)
                    file.save(os.path.join(path, filename))
                    profile.selfie_path = f'selfies/{filename}'

            profile.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('worker_profile'))

        except Exception:
            db.session.rollback()
            flash('Update failed. Please try again.', 'error')

    return render_template('worker/edit_profile.html', worker=profile, user=current_user)

@app.route('/worker/jobs')
@login_required
@worker_required
def worker_jobs():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('worker_dashboard'))
    matches = Match.query.filter_by(worker_profile_id=profile.id) \
        .order_by(Match.updated_at.desc()).all()
    return render_template('worker/jobs.html', worker=profile, user=current_user, matches=matches)

@app.route('/worker/messages')
@login_required
@worker_required
def worker_messages():
    return render_template('worker/messages.html', user=current_user)

@app.route('/worker/reviews')
@login_required
@worker_required
def worker_reviews():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('worker_dashboard'))
    reviews = Review.query.filter_by(worker_profile_id=profile.id) \
        .order_by(Review.created_at.desc()).all()
    return render_template('worker/reviews.html', worker=profile, user=current_user, reviews=reviews)

@app.route('/worker/settings')
@login_required
@worker_required
def worker_settings():
    return render_template('worker/settings.html', user=current_user)

@app.route('/worker/toggle-availability', methods=['POST'])
@login_required
@worker_required
def toggle_availability():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if profile:
        profile.availability_status = 'unavailable' if profile.availability_status == 'available' else 'available'
        db.session.commit()
        flash(f'Status changed to {profile.availability_status}.', 'success')
    return redirect(url_for('worker_dashboard'))

# ----------------------------------------------------------------------
# Employer routes
# ----------------------------------------------------------------------
@app.route('/register/employer', methods=['GET', 'POST'])
def register_employer():
    if current_user.is_authenticated:
        return redirect(url_for('employer_dashboard'))

    if request.method == 'POST':
        data = request.form
        errors = []

        if not data.get('full_name', '').strip() or len(data.get('full_name', '').strip()) < 3:
            errors.append('Full name is required (minimum 3 characters).')
        if not data.get('email') or '@' not in data.get('email', ''):
            errors.append('A valid email address is required.')
        if User.query.filter_by(email=data.get('email', '').strip().lower()).first():
            errors.append('Email is already registered.')
        if not data.get('phone', '').strip():
            errors.append('Phone number is required.')
        if not data.get('password') or len(data.get('password', '')) < 8:
            errors.append('Password must be at least 8 characters.')
        if data.get('password') != data.get('confirm_password', ''):
            errors.append('Passwords do not match.')
        if not data.get('country'):
            errors.append('Country is required.')
        if not data.get('county'):
            errors.append('County/region is required.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('employer/register.html')

        try:
            user = User(
                email=data.get('email', '').strip().lower(),
                phone=data.get('phone', '').strip(),
                full_name=data.get('full_name', '').strip(),
                role='employer'
            )
            user.set_password(data.get('password', ''))
            db.session.add(user)
            db.session.flush()

            employer_profile = EmployerProfile(
                user_id=user.id,
                company_name=data.get('company_name', '').strip() or None,
                country=data.get('country', 'Kenya'),
                county=data.get('county'),
                city=data.get('city', '').strip() or None
            )
            db.session.add(employer_profile)
            db.session.commit()

            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('employer_dashboard'))

        except Exception:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')

    return render_template('employer/register.html')

@app.route('/employer/dashboard')
@login_required
@employer_required
def employer_dashboard():
    profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('register_employer'))

    active_jobs = JobPosting.query.filter_by(employer_id=current_user.id, is_active=True, is_filled=False).count()
    total_jobs = JobPosting.query.filter_by(employer_id=current_user.id).count()
    recent_jobs = JobPosting.query.filter_by(employer_id=current_user.id) \
        .order_by(JobPosting.created_at.desc()).limit(10).all()

    # Workers from the same country
    available_workers = WorkerProfile.query.filter_by(
        availability_status='available',
        country=profile.country
    ).order_by(WorkerProfile.rating_average.desc()).limit(10).all()

    return render_template(
        'employer/dashboard.html',
        employer=profile,
        user=current_user,
        active_jobs=active_jobs,
        total_jobs=total_jobs,
        recent_jobs=recent_jobs,
        available_workers=available_workers
    )

@app.route('/employer/profile')
@login_required
@employer_required
def employer_profile():
    profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('employer_dashboard'))
    return render_template('employer/profile.html', employer=profile, user=current_user)

@app.route('/employer/profile/edit', methods=['GET', 'POST'])
@login_required
@employer_required
def edit_employer_profile():
    profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        try:
            profile.company_name = request.form.get('company_name', profile.company_name)
            profile.country = request.form.get('country', profile.country)
            profile.county = request.form.get('county', profile.county)
            profile.city = request.form.get('city', profile.city)
            current_user.full_name = request.form.get('full_name', current_user.full_name)
            current_user.phone = request.form.get('phone', current_user.phone)
            db.session.commit()
            flash('Profile updated!', 'success')
            return redirect(url_for('employer_profile'))
        except Exception:
            db.session.rollback()
            flash('Update failed.', 'error')
    return render_template('employer/edit_profile.html', employer=profile, user=current_user)

@app.route('/employer/messages')
@login_required
@employer_required
def employer_messages():
    return render_template('employer/messages.html', user=current_user)

@app.route('/employer/settings')
@login_required
@employer_required
def employer_settings():
    return render_template('employer/settings.html', user=current_user)

# ----------------------------------------------------------------------
# Job posting and application routes
# ----------------------------------------------------------------------
@app.route('/job/create', methods=['GET', 'POST'])
@login_required
@employer_required
def create_job():
    if request.method == 'POST':
        data = request.form
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        service_type_needed = data.get('service_type_needed', '')
        location_name = data.get('location_name', '')
        offered_pay_rate = float(data.get('offered_pay_rate', 0))

        if not all([title, description, service_type_needed, location_name]):
            return jsonify({'success': False, 'message': 'Please fill all required fields.'})

        # Inherit employer's country/county
        employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
        job = JobPosting(
            employer_id=current_user.id,
            title=title,
            description=description,
            service_type_needed=service_type_needed,
            location_name=location_name,
            offered_pay_rate=offered_pay_rate,
            pay_period=data.get('pay_period', 'hourly'),
            country=employer_profile.country if employer_profile else 'Kenya',
            county=employer_profile.county if employer_profile else None
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return jsonify({'success': True, 'message': 'Job posted!', 'job_id': job.id})

    return render_template('job/create.html', user=current_user)

@app.route('/employer/jobs')
@login_required
@employer_required
def my_jobs():
    jobs = JobPosting.query.filter_by(employer_id=current_user.id) \
        .order_by(JobPosting.created_at.desc()).all()
    return render_template('job/my_jobs.html', jobs=jobs, user=current_user)

@app.route('/job/browse')
def browse_jobs():
    return render_template('job/browse.html')

@app.route('/job/<int:job_id>')
@login_required
def view_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    return render_template('job/view.html', job=job, user=current_user)

@app.route('/job/<int:job_id>/apply')
@login_required
@worker_required
def apply_for_job(job_id):
    worker = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if Match.query.filter_by(job_posting_id=job_id, worker_profile_id=worker.id).first():
        flash('You have already applied for this job!', 'info')
    else:
        db.session.add(Match(job_posting_id=job_id, worker_profile_id=worker.id, status='applied'))
        db.session.commit()
        flash('Application submitted successfully!', 'success')
    return redirect(url_for('browse_jobs'))

@app.route('/job/<int:job_id>/close')
@login_required
@employer_required
def close_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    if job.employer_id == current_user.id:
        job.is_active = False
        job.closed_at = datetime.utcnow()
        db.session.commit()
        flash('Job closed.', 'success')
    return redirect(url_for('my_jobs'))

@app.route('/job/<int:job_id>/delete')
@login_required
@employer_required
def delete_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    if job.employer_id == current_user.id:
        job.is_active = False
        job.is_filled = True
        job.closed_at = datetime.utcnow()
        db.session.commit()
        flash('Job deleted.', 'success')
    return redirect(url_for('my_jobs'))

@app.route('/job/<int:job_id>/reopen')
@login_required
@employer_required
def reopen_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    if job.employer_id == current_user.id:
        job.is_active = True
        job.closed_at = None
        db.session.commit()
        flash('Job reopened.', 'success')
    return redirect(url_for('my_jobs'))

@app.route('/job/<int:job_id>/matches')
@login_required
def view_matches(job_id):
    job = JobPosting.query.get_or_404(job_id)
    matches = Match.query.filter_by(job_posting_id=job_id) \
        .order_by(Match.match_score.desc()).all()
    return render_template('job/matches.html', job=job, matches=matches, user=current_user)

# ----------------------------------------------------------------------
# Match and review routes
# ----------------------------------------------------------------------
@app.route('/match/create/<int:job_id>/<int:worker_id>')
@login_required
def create_match(job_id, worker_id):
    if not Match.query.filter_by(job_posting_id=job_id, worker_profile_id=worker_id).first():
        db.session.add(Match(job_posting_id=job_id, worker_profile_id=worker_id, match_score=70))
        db.session.commit()
        flash('Match created!', 'success')
    return redirect(url_for('view_matches', job_id=job_id))

@app.route('/match/<int:match_id>/status/<string:status>')
@login_required
def update_match_status(match_id, status):
    match = Match.query.get_or_404(match_id)
    if status in ['contacted', 'interviewed', 'hired', 'completed', 'rejected']:
        match.status = status
        match.updated_at = datetime.utcnow()
        if status == 'completed':
            job = JobPosting.query.get(match.job_posting_id)
            if job:
                job.is_filled = True
                job.is_active = False
            worker = WorkerProfile.query.get(match.worker_profile_id)
            if worker:
                worker.completed_jobs += 1
        db.session.commit()
        flash(f'Status updated to {status}.', 'success')
    return redirect(url_for('view_matches', job_id=match.job_posting_id))

@app.route('/review/create/<int:match_id>', methods=['POST'])
@login_required
def create_review(match_id):
    try:
        match = Match.query.get_or_404(match_id)
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '').strip()
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5.'})

        if Review.query.filter_by(
            job_posting_id=match.job_posting_id,
            reviewer_id=current_user.id,
            worker_profile_id=match.worker_profile_id
        ).first():
            return jsonify({'success': False, 'message': 'You have already reviewed this worker.'})

        db.session.add(Review(
            job_posting_id=match.job_posting_id,
            reviewer_id=current_user.id,
            worker_profile_id=match.worker_profile_id,
            rating=rating,
            comment=comment
        ))
        worker = WorkerProfile.query.get(match.worker_profile_id)
        if worker:
            worker.total_reviews += 1
            worker.rating_average = ((worker.rating_average * (worker.total_reviews - 1)) + rating) / worker.total_reviews
        db.session.commit()
        return jsonify({'success': True, 'message': 'Review submitted!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# ----------------------------------------------------------------------
# Search routes
# ----------------------------------------------------------------------
@app.route('/search/workers')
def search_workers():
    return render_template('search/workers.html')

@app.route('/search/jobs')
def search_jobs_page():
    return render_template('job/browse.html')

# ----------------------------------------------------------------------
# Messaging and notifications
# ----------------------------------------------------------------------
@app.route('/messages/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id):
    other = User.query.get_or_404(user_id)
    if request.method == 'POST':
        content = request.form.get('message', '').strip()
        if content:
            db.session.add(Message(sender_id=current_user.id, receiver_id=user_id, content=content))
            db.session.commit()

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    unread = Message.query.filter_by(receiver_id=current_user.id, sender_id=user_id, is_read=False).all()
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()

    return render_template('chat.html', messages=messages, other_user=other, user=current_user)

@app.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()).all()
    for n in notifs:
        if not n.is_read:
            n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs, user=current_user)

# ----------------------------------------------------------------------
# Admin routes
# ----------------------------------------------------------------------
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', 'all')
    search = request.args.get('q', '').strip()

    q = User.query
    if role_filter in ['worker', 'employer']:
        q = q.filter_by(role=role_filter)
    if search:
        q = q.filter(User.full_name.ilike(f'%{search}%'))

    users = q.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'admin/dashboard.html',
        users=users,
        total_users=User.query.count(),
        total_workers=User.query.filter_by(role='worker').count(),
        total_employers=User.query.filter_by(role='employer').count(),
        total_jobs=JobPosting.query.count(),
        active_jobs=JobPosting.query.filter_by(is_active=True, is_filled=False).count(),
        completed_jobs=Match.query.filter_by(status='completed').count(),
        total_matches=Match.query.count(),
        total_reviews=Review.query.count(),
        role_filter=role_filter,
        search_query=search
    )

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', 'all')
    search = request.args.get('q', '').strip()

    q = User.query
    if role_filter in ['worker', 'employer']:
        q = q.filter_by(role=role_filter)
    if search:
        q = q.filter(User.full_name.ilike(f'%{search}%'))

    users = q.order_by(User.created_at.desc()).paginate(page=page, per_page=30, error_out=False)

    return render_template(
        'admin/users.html',
        users=users,
        role_filter=role_filter,
        search_query=search
    )

@app.route('/admin/user/<int:user_id>')
@login_required
@admin_required
def admin_view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('admin/view_user.html', user=user)

@app.route('/admin/user/<int:user_id>/verify')
@login_required
@admin_required
def admin_verify_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'worker' and user.worker_profile:
        user.worker_profile.id_verified = True
        user.is_verified = True
        db.session.commit()
        flash(f'{user.full_name} verified.', 'success')
    return redirect(url_for('admin_view_user', user_id=user_id))

@app.route('/admin/user/<int:user_id>/toggle-status')
@login_required
@admin_required
def admin_toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'{user.full_name} {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin_view_user', user_id=user_id))

@app.route('/admin/stats')
@login_required
@admin_required
def admin_stats():
    from sqlalchemy import func
    stats = {
        'total_users': User.query.count(),
        'total_workers': User.query.filter_by(role='worker').count(),
        'total_employers': User.query.filter_by(role='employer').count(),
        'verified_workers': WorkerProfile.query.filter_by(id_verified=True).count(),
        'total_jobs': JobPosting.query.count(),
        'active_jobs': JobPosting.query.filter_by(is_active=True, is_filled=False).count(),
        'completed_jobs': Match.query.filter_by(status='completed').count(),
        'total_matches': Match.query.count(),
        'total_reviews': Review.query.count(),
        'total_messages': Message.query.count(),
        'avg_rating': round(db.session.query(func.avg(WorkerProfile.rating_average)).scalar() or 0, 2),
        'recent_registrations': User.query.filter(User.created_at >= datetime.utcnow() - timedelta(days=30)).count(),
        'jobs_by_service': dict(
            db.session.query(JobPosting.service_type_needed, func.count(JobPosting.id))
            .group_by(JobPosting.service_type_needed).all()
        )
    }
    logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(50).all()
    return render_template('admin/stats.html', stats=stats, logs=logs)

# ----------------------------------------------------------------------
# API routes
# ----------------------------------------------------------------------
@app.route('/api/check-auth')
def api_check_auth():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'full_name': current_user.full_name,
                'role': current_user.role,
                'email': current_user.email
            }
        })
    return jsonify({'authenticated': False})

@app.route('/api/stats')
def api_stats():
    return jsonify({'success': True, 'stats': {
        'total_users': User.query.count(),
        'total_workers': User.query.filter_by(role='worker').count(),
        'total_employers': User.query.filter_by(role='employer').count(),
        'active_jobs': JobPosting.query.filter_by(is_active=True, is_filled=False).count(),
        'completed_jobs': Match.query.filter_by(status='completed').count()
    }})

@app.route('/api/jobs')
def api_jobs():
    q = JobPosting.query.filter_by(is_active=True, is_filled=False)

    # Regional filtering: if worker logged in, restrict to same country
    if current_user.is_authenticated and current_user.role == 'worker':
        worker = WorkerProfile.query.filter_by(user_id=current_user.id).first()
        if worker and worker.country:
            q = q.filter_by(country=worker.country)

    if request.args.get('service_type'):
        q = q.filter_by(service_type_needed=request.args.get('service_type'))
    if request.args.get('county'):
        q = q.filter_by(county=request.args.get('county'))
    if request.args.get('q'):
        q = q.filter(JobPosting.title.ilike(f"%{request.args.get('q')}%"))
    if request.args.get('sort') == 'high':
        q = q.order_by(JobPosting.offered_pay_rate.desc())
    else:
        q = q.order_by(JobPosting.created_at.desc())

    jobs = []
    for j in q.limit(50).all():
        emp = User.query.get(j.employer_id)
        jobs.append({
            'id': j.id,
            'title': j.title,
            'description': j.description[:150],
            'service_type_needed': j.service_type_needed,
            'service_name': j.service_type_needed.replace('_', ' ').title(),
            'location_name': j.location_name,
            'county': j.county or '',
            'country': j.country or 'Kenya',
            'offered_pay_rate': j.offered_pay_rate,
            'pay_period': j.pay_period,
            'time_ago': _time_ago(j.created_at),
            'employer_name': emp.full_name if emp else 'Anonymous',
            'application_count': Match.query.filter_by(job_posting_id=j.id, status='applied').count()
        })
    return jsonify({'success': True, 'jobs': jobs, 'total': len(jobs)})

@app.route('/api/workers')
def api_workers():
    q = WorkerProfile.query.filter_by(availability_status='available')

    # Regional filtering: if employer logged in, restrict to same country
    if current_user.is_authenticated and current_user.role == 'employer':
        emp = EmployerProfile.query.filter_by(user_id=current_user.id).first()
        if emp and emp.country:
            q = q.filter_by(country=emp.country)

    if request.args.get('service_type'):
        q = q.filter_by(service_type=request.args.get('service_type'))
    if request.args.get('county'):
        q = q.filter_by(county=request.args.get('county'))
    if request.args.get('q'):
        q = q.join(User).filter(User.full_name.ilike(f"%{request.args.get('q')}%"))
    if request.args.get('sort') == 'experience':
        q = q.order_by(WorkerProfile.experience_years.desc())
    else:
        q = q.order_by(WorkerProfile.rating_average.desc())

    workers = []
    for w in q.limit(50).all():
        u = User.query.get(w.user_id)
        workers.append({
            'id': w.id,
            'user_id': w.user_id,
            'full_name': u.full_name if u else 'Unknown',
            'service_type': w.service_type,
            'service_name': w.service_type.replace('_', ' ').title(),
            'experience_years': w.experience_years,
            'expected_pay_rate': w.expected_pay_rate,
            'pay_period': w.pay_period,
            'rating_average': round(w.rating_average, 1),
            'total_reviews': w.total_reviews,
            'locations': w.get_locations_list(),
            'county': w.county or '',
            'country': w.country or 'Kenya',
            'id_verified': w.id_verified,
            'selfie_path': w.selfie_path
        })
    return jsonify({'success': True, 'workers': workers, 'total': len(workers)})

@app.route('/api/employer/dashboard')
@login_required
@employer_required
def api_employer_dashboard():
    job_ids = [j.id for j in JobPosting.query.filter_by(employer_id=current_user.id).all()]
    return jsonify({'success': True, 'stats': {
        'active_jobs': JobPosting.query.filter_by(employer_id=current_user.id, is_active=True, is_filled=False).count(),
        'total_jobs': JobPosting.query.filter_by(employer_id=current_user.id).count(),
        'total_applications': Match.query.filter(
            Match.job_posting_id.in_(job_ids), Match.status == 'applied'
        ).count() if job_ids else 0,
        'total_hired': Match.query.filter(
            Match.job_posting_id.in_(job_ids), Match.status == 'hired'
        ).count() if job_ids else 0
    }})

@app.route('/api/worker/dashboard')
@login_required
@worker_required
def api_worker_dashboard():
    wp = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not wp:
        return jsonify({'success': False})
    return jsonify({'success': True, 'stats': {
        'completed_jobs': Match.query.filter_by(worker_profile_id=wp.id, status='completed').count(),
        'pending_applications': Match.query.filter_by(worker_profile_id=wp.id, status='applied').count(),
        'active_matches': Match.query.filter(
            Match.worker_profile_id == wp.id,
            Match.status.in_(['contacted', 'interviewed', 'hired'])
        ).count(),
        'rating': round(wp.rating_average, 1),
        'total_reviews': wp.total_reviews,
        'profile_completion': (20 if wp.bio else 0) + (20 if wp.id_document_path else 0) +
                              (20 if wp.selfie_path else 0) + (20 if wp.get_locations_list() else 0) +
                              (20 if wp.id_verified else 0)
    }})

@app.route('/api/messages/<int:user_id>')
@login_required
def api_conversation(user_id):
    other = User.query.get(user_id)
    if not other:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).limit(100).all()

    unread = Message.query.filter_by(receiver_id=current_user.id, sender_id=user_id, is_read=False).all()
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()

    return jsonify({
        'success': True,
        'messages': [{
            'id': m.id,
            'content': m.content,
            'sender_id': m.sender_id,
            'is_mine': m.sender_id == current_user.id,
            'is_read': m.is_read,
            'created_at': m.created_at.strftime('%H:%M') if m.created_at else None
        } for m in messages],
        'other_user': {'id': other.id, 'full_name': other.full_name, 'role': other.role}
    })

@app.route('/api/messages/send', methods=['POST'])
@login_required
def api_send_message():
    data = request.get_json()
    if not data.get('receiver_id') or not data.get('content', '').strip():
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    msg = Message(
        sender_id=current_user.id,
        receiver_id=data['receiver_id'],
        content=data['content'].strip()
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': {
            'id': msg.id,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%H:%M')
        }
    })

@app.route('/api/notifications')
@login_required
def api_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify({
        'success': True,
        'unread_count': Notification.query.filter_by(user_id=current_user.id, is_read=False).count(),
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'time_ago': _time_ago(n.created_at)
        } for n in notifs]
    })

@app.route('/api/service-types')
def api_service_types():
    types = ['house_help', 'cleaner', 'plumber', 'electrician', 'gardener', 'painter',
             'carpenter', 'mason', 'welder', 'mechanic', 'driver', 'security_guard']
    return jsonify({
        'success': True,
        'services': [{
            'id': t,
            'name': t.replace('_', ' ').title(),
            'worker_count': WorkerProfile.query.filter_by(
                service_type=t, availability_status='available'
            ).count()
        } for t in types]
    })

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.get_json()
    print(f"Contact: {data.get('name')} - {data.get('email')} - {data.get('subject')}: {data.get('message')}")
    return jsonify({'success': True, 'message': 'Message received!'})

# ----------------------------------------------------------------------
# Seed data route
# ----------------------------------------------------------------------
@app.route('/seed-data')
def seed_data():
    if User.query.filter_by(role='worker').first():
        return jsonify({'success': False, 'message': 'Data already exists! Delete database first.'})

    workers = [
        ('John Kamau', 'john@test.com', 'plumber', 8, 15, 'Nairobi', 'Kenya'),
        ('Mary Wanjiku', 'mary@test.com', 'cleaner', 5, 10, 'Nairobi', 'Kenya'),
        ('Peter Omondi', 'peter@test.com', 'electrician', 12, 20, 'Nairobi', 'Kenya'),
        ('Jane Njeri', 'jane@test.com', 'house_help', 6, 12, 'Nairobi', 'Kenya'),
        ('David Muthoka', 'david@test.com', 'gardener', 4, 8, 'Nairobi', 'Kenya'),
        ('Grace Akinyi', 'grace@test.com', 'painter', 10, 18, 'Mombasa', 'Kenya'),
        ('Samuel Kiprotich', 'samuel@test.com', 'carpenter', 15, 25, 'Nakuru', 'Kenya'),
        ('Alice Chebet', 'alice@test.com', 'driver', 7, 10, 'Eldoret', 'Kenya')
    ]

    for name, email, svc, exp, rate, county, country in workers:
        u = User(email=email, phone=f'+2547{10000000 + len(name)}', full_name=name, role='worker')
        u.set_password('password123')
        db.session.add(u)
        db.session.flush()
        db.session.add(WorkerProfile(
            user_id=u.id,
            service_type=svc,
            experience_years=exp,
            expected_pay_rate=rate,
            pay_period='hourly',
            availability_status='available',
            preferred_locations=json.dumps(['Downtown', 'Westlands', 'Kilimani']),
            rating_average=round(3.5 + exp * 0.1, 1),
            total_reviews=exp * 2,
            completed_jobs=exp * 3,
            id_verified=True,
            country=country,
            county=county
        ))

    emp = User(email='employer@test.com', phone='+254700000001', full_name='ABC Company', role='employer')
    emp.set_password('password123')
    db.session.add(emp)
    db.session.flush()
    db.session.add(EmployerProfile(
        user_id=emp.id,
        company_name='ABC Company',
        city='Nairobi',
        country='Kenya',
        county='Nairobi'
    ))

    jobs = [
        ('Need Plumber for Kitchen', 'plumber', 'Westlands', 15, 'Nairobi', 'Kenya'),
        ('House Cleaner Needed', 'cleaner', 'Kilimani', 10, 'Nairobi', 'Kenya'),
        ('Electrician for Office', 'electrician', 'Downtown', 22, 'Nairobi', 'Kenya'),
        ('House Help for Family', 'house_help', 'Karen', 12, 'Nairobi', 'Kenya'),
        ('Gardener Large Compound', 'gardener', 'Lavington', 9, 'Nairobi', 'Kenya'),
        ('Interior Painter', 'painter', 'Parklands', 16, 'Nairobi', 'Kenya'),
        ('Carpenter Custom Wardrobe', 'carpenter', 'Kileleshwa', 20, 'Nairobi', 'Kenya'),
        ('Driver Family Transport', 'driver', 'Runda', 8, 'Nairobi', 'Kenya')
    ]

    for title, svc, loc, rate, county, country in jobs:
        db.session.add(JobPosting(
            employer_id=emp.id,
            title=title,
            description=f'Looking for reliable {svc} in {loc}. Must have experience and good references.',
            service_type_needed=svc,
            location_name=loc,
            offered_pay_rate=rate,
            is_active=True,
            country=country,
            county=county
        ))

    db.session.commit()
    return jsonify({'success': True, 'message': f'Seeded {len(workers)} workers and {len(jobs)} jobs! Use password123 to login.'})

# ----------------------------------------------------------------------
# Error handlers
# ----------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 THE WORKING MAN PLATFORM")
    print(f"📱 URL: http://localhost:5000")
    print(f"🔑 Admin: http://localhost:5000/admin")
    print(f"🌱 Seed: http://localhost:5000/seed-data")
    print("=" * 60)
    app.run(debug=True, port=5000, host='0.0.0.0')# app.py - The Working Man Platform (Refined & Production-Ready)
import sys
import os
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()

from config import config_by_name
from database.models import (
    db, bcrypt, User, WorkerProfile, EmployerProfile,
    JobPosting, Match, Review, Message, Notification, AdminLog
)

# ----------------------------------------------------------------------
# App factory and configuration
# ----------------------------------------------------------------------
app = Flask(__name__)

config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config_by_name.get(config_name, config_by_name['development']))

# Ensure upload directories exist
upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
os.makedirs(upload_folder, exist_ok=True)
os.makedirs(os.path.join(upload_folder, 'documents'), exist_ok=True)
os.makedirs(os.path.join(upload_folder, 'selfies'), exist_ok=True)

# Initialise extensions
db.init_app(app)
bcrypt.init_app(app)

# Initialise login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))   # SQLAlchemy 2.0 style

# ----------------------------------------------------------------------
# Helper functions and decorators
# ----------------------------------------------------------------------
def allowed_file(filename):
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def worker_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'worker':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorator

def employer_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'employer':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorator

def admin_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorator

def _time_ago(dt):
    if not dt:
        return 'Unknown'
    diff = datetime.utcnow() - dt
    if diff.days > 30:
        return f"{diff.days // 30}mo ago"
    if diff.days > 0:
        return f"{diff.days}d ago"
    if diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    return 'Just now'

# ----------------------------------------------------------------------
# Database initialisation and admin auto-creation
# ----------------------------------------------------------------------
with app.app_context():
    db.create_all()
    print("✅ Database ready")

    # Create default admin if it doesn't exist
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@workingman.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'Admin@123')
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            email=admin_email,
            phone='+254700000000',
            full_name='System Admin',
            role='admin',
            is_verified=True,
            is_active=True
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin created: {admin_email}")

# ----------------------------------------------------------------------
# Context processor for global template variables
# ----------------------------------------------------------------------
@app.context_processor
def inject_globals():
    unread_notifications = 0
    unread_messages = 0
    if current_user.is_authenticated:
        try:
            unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            unread_messages = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
        except Exception:
            pass
    return {
        'now': datetime.utcnow(),
        'unread_notifications': unread_notifications,
        'unread_messages': unread_messages,
    }

# ----------------------------------------------------------------------
# Main routes
# ----------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/help-center')
def help_center():
    return render_template('help_center.html')

@app.route('/safety-tips')
def safety_tips():
    return render_template('safety_tips.html')

@app.route('/success-stories')
def success_stories():
    return render_template('success_stories.html')

# ----------------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({
            'success': True,
            'user': {'id': current_user.id, 'full_name': current_user.full_name, 'role': current_user.role}
        })

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=bool(request.form.get('remember')))
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f'Welcome back, {user.full_name}!', 'success')
            return jsonify({
                'success': True,
                'user': {'id': user.id, 'full_name': user.full_name, 'role': user.role}
            })

        flash('Invalid email or password.', 'error')
        return jsonify({'success': False, 'message': 'Invalid email or password'})

    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if User.query.filter_by(email=email).first():
            flash('Password reset instructions sent.', 'success')
        else:
            flash('No account found.', 'error')
        return redirect(url_for('login'))
    return render_template('auth/forgot_password.html')

# ----------------------------------------------------------------------
# Dashboard (role-based redirect)
# ----------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'worker':
        return redirect(url_for('worker_dashboard'))
    elif current_user.role == 'employer':
        return redirect(url_for('employer_dashboard'))
    elif current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index'))

# ----------------------------------------------------------------------
# Worker routes
# ----------------------------------------------------------------------
@app.route('/register/worker', methods=['GET', 'POST'])
def register_worker():
    if current_user.is_authenticated:
        return redirect(url_for('worker_dashboard'))

    if request.method == 'POST':
        data = request.form
        errors = []

        if not data.get('full_name', '').strip() or len(data.get('full_name', '').strip()) < 3:
            errors.append('Full name is required (minimum 3 characters).')
        if not data.get('email') or '@' not in data.get('email', ''):
            errors.append('A valid email address is required.')
        if User.query.filter_by(email=data.get('email', '').strip().lower()).first():
            errors.append('Email is already registered.')
        if not data.get('phone', '').strip():
            errors.append('Phone number is required.')
        if not data.get('password') or len(data.get('password', '')) < 8:
            errors.append('Password must be at least 8 characters.')
        if data.get('password') != data.get('confirm_password', ''):
            errors.append('Passwords do not match.')
        if not data.get('service_type'):
            errors.append('Service type is required.')
        if not data.get('country'):
            errors.append('Country is required.')
        if not data.get('county'):
            errors.append('County/region is required.')
        if not data.getlist('preferred_locations'):
            errors.append('Select at least one work location.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('worker/register.html')

        try:
            user = User(
                email=data.get('email', '').strip().lower(),
                phone=data.get('phone', '').strip(),
                full_name=data.get('full_name', '').strip(),
                role='worker'
            )
            user.set_password(data.get('password', ''))
            db.session.add(user)
            db.session.flush()

            try:
                exp_years = int(data.get('experience_years', 0))
                pay_rate = float(data.get('expected_pay_rate', 0))
            except (ValueError, TypeError):
                exp_years = 0
                pay_rate = 0

            profile = WorkerProfile(
                user_id=user.id,
                service_type=data.get('service_type'),
                experience_years=exp_years,
                bio=data.get('bio', '').strip() or None,
                expected_pay_rate=pay_rate,
                pay_period=data.get('pay_period', 'hourly'),
                availability_status='available',
                preferred_locations=json.dumps(data.getlist('preferred_locations')),
                country=data.get('country', 'Kenya'),
                county=data.get('county'),
                city=data.get('city', '').strip() or None
            )
            db.session.add(profile)
            db.session.commit()

            login_user(user)
            flash(f'Registration successful! Welcome, {user.full_name}.', 'success')
            return redirect(url_for('worker_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')

    return render_template('worker/register.html')

@app.route('/worker/dashboard')
@login_required
@worker_required
def worker_dashboard():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('register_worker'))

    completed_jobs = Match.query.filter_by(worker_profile_id=profile.id, status='completed').count()
    pending_applications = Match.query.filter_by(worker_profile_id=profile.id, status='applied').count()
    active_matches = Match.query.filter(
        Match.worker_profile_id == profile.id,
        Match.status.in_(['contacted', 'interviewed', 'hired'])
    ).count()

    recent_matches = Match.query.filter_by(worker_profile_id=profile.id) \
        .order_by(Match.updated_at.desc()).limit(10).all()

    # Only show jobs from the worker's country (and ideally same county)
    available_jobs = JobPosting.query.filter_by(
        service_type_needed=profile.service_type,
        is_active=True,
        is_filled=False,
        country=profile.country
    ).order_by(JobPosting.created_at.desc()).limit(10).all()

    return render_template(
        'worker/dashboard.html',
        worker=profile,
        user=current_user,
        completed_jobs=completed_jobs,
        pending_matches=pending_applications,
        active_matches=active_matches,
        recent_matches=recent_matches,
        available_jobs=available_jobs
    )

@app.route('/worker/profile')
@login_required
@worker_required
def worker_profile():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('worker_dashboard'))
    reviews = Review.query.filter_by(worker_profile_id=profile.id) \
        .order_by(Review.created_at.desc()).limit(10).all()
    return render_template('worker/profile.html', worker=profile, user=current_user, reviews=reviews)

@app.route('/worker/profile/create')
@login_required
@worker_required
def create_worker_profile_full():
    return render_template('worker/create_profile.html', user=current_user)

@app.route('/worker/profile/edit', methods=['GET', 'POST'])
@login_required
@worker_required
def edit_worker_profile():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('worker_dashboard'))

    if request.method == 'POST':
        try:
            profile.service_type = request.form.get('service_type', profile.service_type)
            profile.experience_years = int(request.form.get('experience_years', profile.experience_years))
            profile.bio = request.form.get('bio', profile.bio)
            profile.expected_pay_rate = float(request.form.get('expected_pay_rate', profile.expected_pay_rate))
            profile.pay_period = request.form.get('pay_period', profile.pay_period)
            profile.availability_status = request.form.get('availability_status', profile.availability_status)

            # Optional country/county update
            if request.form.get('country'):
                profile.country = request.form.get('country')
            if request.form.get('county'):
                profile.county = request.form.get('county')
            if request.form.get('city'):
                profile.city = request.form.get('city')

            locations = request.form.getlist('preferred_locations')
            if locations:
                profile.preferred_locations = json.dumps(locations)

            if 'selfie' in request.files:
                file = request.files['selfie']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{current_user.id}_selfie_{file.filename}")
                    path = os.path.join(app.config['UPLOAD_FOLDER'], 'selfies')
                    os.makedirs(path, exist_ok=True)
                    file.save(os.path.join(path, filename))
                    profile.selfie_path = f'selfies/{filename}'

            profile.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('worker_profile'))

        except Exception:
            db.session.rollback()
            flash('Update failed. Please try again.', 'error')

    return render_template('worker/edit_profile.html', worker=profile, user=current_user)

@app.route('/worker/jobs')
@login_required
@worker_required
def worker_jobs():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('worker_dashboard'))
    matches = Match.query.filter_by(worker_profile_id=profile.id) \
        .order_by(Match.updated_at.desc()).all()
    return render_template('worker/jobs.html', worker=profile, user=current_user, matches=matches)

@app.route('/worker/messages')
@login_required
@worker_required
def worker_messages():
    return render_template('worker/messages.html', user=current_user)

@app.route('/worker/reviews')
@login_required
@worker_required
def worker_reviews():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('worker_dashboard'))
    reviews = Review.query.filter_by(worker_profile_id=profile.id) \
        .order_by(Review.created_at.desc()).all()
    return render_template('worker/reviews.html', worker=profile, user=current_user, reviews=reviews)

@app.route('/worker/settings')
@login_required
@worker_required
def worker_settings():
    return render_template('worker/settings.html', user=current_user)

@app.route('/worker/toggle-availability', methods=['POST'])
@login_required
@worker_required
def toggle_availability():
    profile = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if profile:
        profile.availability_status = 'unavailable' if profile.availability_status == 'available' else 'available'
        db.session.commit()
        flash(f'Status changed to {profile.availability_status}.', 'success')
    return redirect(url_for('worker_dashboard'))

# ----------------------------------------------------------------------
# Employer routes
# ----------------------------------------------------------------------
@app.route('/register/employer', methods=['GET', 'POST'])
def register_employer():
    if current_user.is_authenticated:
        return redirect(url_for('employer_dashboard'))

    if request.method == 'POST':
        data = request.form
        errors = []

        if not data.get('full_name', '').strip() or len(data.get('full_name', '').strip()) < 3:
            errors.append('Full name is required (minimum 3 characters).')
        if not data.get('email') or '@' not in data.get('email', ''):
            errors.append('A valid email address is required.')
        if User.query.filter_by(email=data.get('email', '').strip().lower()).first():
            errors.append('Email is already registered.')
        if not data.get('phone', '').strip():
            errors.append('Phone number is required.')
        if not data.get('password') or len(data.get('password', '')) < 8:
            errors.append('Password must be at least 8 characters.')
        if data.get('password') != data.get('confirm_password', ''):
            errors.append('Passwords do not match.')
        if not data.get('country'):
            errors.append('Country is required.')
        if not data.get('county'):
            errors.append('County/region is required.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('employer/register.html')

        try:
            user = User(
                email=data.get('email', '').strip().lower(),
                phone=data.get('phone', '').strip(),
                full_name=data.get('full_name', '').strip(),
                role='employer'
            )
            user.set_password(data.get('password', ''))
            db.session.add(user)
            db.session.flush()

            employer_profile = EmployerProfile(
                user_id=user.id,
                company_name=data.get('company_name', '').strip() or None,
                country=data.get('country', 'Kenya'),
                county=data.get('county'),
                city=data.get('city', '').strip() or None
            )
            db.session.add(employer_profile)
            db.session.commit()

            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('employer_dashboard'))

        except Exception:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')

    return render_template('employer/register.html')

@app.route('/employer/dashboard')
@login_required
@employer_required
def employer_dashboard():
    profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('register_employer'))

    active_jobs = JobPosting.query.filter_by(employer_id=current_user.id, is_active=True, is_filled=False).count()
    total_jobs = JobPosting.query.filter_by(employer_id=current_user.id).count()
    recent_jobs = JobPosting.query.filter_by(employer_id=current_user.id) \
        .order_by(JobPosting.created_at.desc()).limit(10).all()

    # Workers from the same country
    available_workers = WorkerProfile.query.filter_by(
        availability_status='available',
        country=profile.country
    ).order_by(WorkerProfile.rating_average.desc()).limit(10).all()

    return render_template(
        'employer/dashboard.html',
        employer=profile,
        user=current_user,
        active_jobs=active_jobs,
        total_jobs=total_jobs,
        recent_jobs=recent_jobs,
        available_workers=available_workers
    )

@app.route('/employer/profile')
@login_required
@employer_required
def employer_profile():
    profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('employer_dashboard'))
    return render_template('employer/profile.html', employer=profile, user=current_user)

@app.route('/employer/profile/edit', methods=['GET', 'POST'])
@login_required
@employer_required
def edit_employer_profile():
    profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        try:
            profile.company_name = request.form.get('company_name', profile.company_name)
            profile.country = request.form.get('country', profile.country)
            profile.county = request.form.get('county', profile.county)
            profile.city = request.form.get('city', profile.city)
            current_user.full_name = request.form.get('full_name', current_user.full_name)
            current_user.phone = request.form.get('phone', current_user.phone)
            db.session.commit()
            flash('Profile updated!', 'success')
            return redirect(url_for('employer_profile'))
        except Exception:
            db.session.rollback()
            flash('Update failed.', 'error')
    return render_template('employer/edit_profile.html', employer=profile, user=current_user)

@app.route('/employer/messages')
@login_required
@employer_required
def employer_messages():
    return render_template('employer/messages.html', user=current_user)

@app.route('/employer/settings')
@login_required
@employer_required
def employer_settings():
    return render_template('employer/settings.html', user=current_user)

# ----------------------------------------------------------------------
# Job posting and application routes
# ----------------------------------------------------------------------
@app.route('/job/create', methods=['GET', 'POST'])
@login_required
@employer_required
def create_job():
    if request.method == 'POST':
        data = request.form
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        service_type_needed = data.get('service_type_needed', '')
        location_name = data.get('location_name', '')
        offered_pay_rate = float(data.get('offered_pay_rate', 0))

        if not all([title, description, service_type_needed, location_name]):
            return jsonify({'success': False, 'message': 'Please fill all required fields.'})

        # Inherit employer's country/county
        employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
        job = JobPosting(
            employer_id=current_user.id,
            title=title,
            description=description,
            service_type_needed=service_type_needed,
            location_name=location_name,
            offered_pay_rate=offered_pay_rate,
            pay_period=data.get('pay_period', 'hourly'),
            country=employer_profile.country if employer_profile else 'Kenya',
            county=employer_profile.county if employer_profile else None
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return jsonify({'success': True, 'message': 'Job posted!', 'job_id': job.id})

    return render_template('job/create.html', user=current_user)

@app.route('/employer/jobs')
@login_required
@employer_required
def my_jobs():
    jobs = JobPosting.query.filter_by(employer_id=current_user.id) \
        .order_by(JobPosting.created_at.desc()).all()
    return render_template('job/my_jobs.html', jobs=jobs, user=current_user)

@app.route('/job/browse')
def browse_jobs():
    return render_template('job/browse.html')

@app.route('/job/<int:job_id>')
@login_required
def view_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    return render_template('job/view.html', job=job, user=current_user)

@app.route('/job/<int:job_id>/apply')
@login_required
@worker_required
def apply_for_job(job_id):
    worker = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if Match.query.filter_by(job_posting_id=job_id, worker_profile_id=worker.id).first():
        flash('You have already applied for this job!', 'info')
    else:
        db.session.add(Match(job_posting_id=job_id, worker_profile_id=worker.id, status='applied'))
        db.session.commit()
        flash('Application submitted successfully!', 'success')
    return redirect(url_for('browse_jobs'))

@app.route('/job/<int:job_id>/close')
@login_required
@employer_required
def close_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    if job.employer_id == current_user.id:
        job.is_active = False
        job.closed_at = datetime.utcnow()
        db.session.commit()
        flash('Job closed.', 'success')
    return redirect(url_for('my_jobs'))

@app.route('/job/<int:job_id>/delete')
@login_required
@employer_required
def delete_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    if job.employer_id == current_user.id:
        job.is_active = False
        job.is_filled = True
        job.closed_at = datetime.utcnow()
        db.session.commit()
        flash('Job deleted.', 'success')
    return redirect(url_for('my_jobs'))

@app.route('/job/<int:job_id>/reopen')
@login_required
@employer_required
def reopen_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    if job.employer_id == current_user.id:
        job.is_active = True
        job.closed_at = None
        db.session.commit()
        flash('Job reopened.', 'success')
    return redirect(url_for('my_jobs'))

@app.route('/job/<int:job_id>/matches')
@login_required
def view_matches(job_id):
    job = JobPosting.query.get_or_404(job_id)
    matches = Match.query.filter_by(job_posting_id=job_id) \
        .order_by(Match.match_score.desc()).all()
    return render_template('job/matches.html', job=job, matches=matches, user=current_user)

# ----------------------------------------------------------------------
# Match and review routes
# ----------------------------------------------------------------------
@app.route('/match/create/<int:job_id>/<int:worker_id>')
@login_required
def create_match(job_id, worker_id):
    if not Match.query.filter_by(job_posting_id=job_id, worker_profile_id=worker_id).first():
        db.session.add(Match(job_posting_id=job_id, worker_profile_id=worker_id, match_score=70))
        db.session.commit()
        flash('Match created!', 'success')
    return redirect(url_for('view_matches', job_id=job_id))

@app.route('/match/<int:match_id>/status/<string:status>')
@login_required
def update_match_status(match_id, status):
    match = Match.query.get_or_404(match_id)
    if status in ['contacted', 'interviewed', 'hired', 'completed', 'rejected']:
        match.status = status
        match.updated_at = datetime.utcnow()
        if status == 'completed':
            job = JobPosting.query.get(match.job_posting_id)
            if job:
                job.is_filled = True
                job.is_active = False
            worker = WorkerProfile.query.get(match.worker_profile_id)
            if worker:
                worker.completed_jobs += 1
        db.session.commit()
        flash(f'Status updated to {status}.', 'success')
    return redirect(url_for('view_matches', job_id=match.job_posting_id))

@app.route('/review/create/<int:match_id>', methods=['POST'])
@login_required
def create_review(match_id):
    try:
        match = Match.query.get_or_404(match_id)
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '').strip()
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5.'})

        if Review.query.filter_by(
            job_posting_id=match.job_posting_id,
            reviewer_id=current_user.id,
            worker_profile_id=match.worker_profile_id
        ).first():
            return jsonify({'success': False, 'message': 'You have already reviewed this worker.'})

        db.session.add(Review(
            job_posting_id=match.job_posting_id,
            reviewer_id=current_user.id,
            worker_profile_id=match.worker_profile_id,
            rating=rating,
            comment=comment
        ))
        worker = WorkerProfile.query.get(match.worker_profile_id)
        if worker:
            worker.total_reviews += 1
            worker.rating_average = ((worker.rating_average * (worker.total_reviews - 1)) + rating) / worker.total_reviews
        db.session.commit()
        return jsonify({'success': True, 'message': 'Review submitted!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# ----------------------------------------------------------------------
# Search routes
# ----------------------------------------------------------------------
@app.route('/search/workers')
def search_workers():
    return render_template('search/workers.html')

@app.route('/search/jobs')
def search_jobs_page():
    return render_template('job/browse.html')

# ----------------------------------------------------------------------
# Messaging and notifications
# ----------------------------------------------------------------------
@app.route('/messages/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id):
    other = User.query.get_or_404(user_id)
    if request.method == 'POST':
        content = request.form.get('message', '').strip()
        if content:
            db.session.add(Message(sender_id=current_user.id, receiver_id=user_id, content=content))
            db.session.commit()

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    unread = Message.query.filter_by(receiver_id=current_user.id, sender_id=user_id, is_read=False).all()
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()

    return render_template('chat.html', messages=messages, other_user=other, user=current_user)

@app.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()).all()
    for n in notifs:
        if not n.is_read:
            n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs, user=current_user)

# ----------------------------------------------------------------------
# Admin routes
# ----------------------------------------------------------------------
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', 'all')
    search = request.args.get('q', '').strip()

    q = User.query
    if role_filter in ['worker', 'employer']:
        q = q.filter_by(role=role_filter)
    if search:
        q = q.filter(User.full_name.ilike(f'%{search}%'))

    users = q.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'admin/dashboard.html',
        users=users,
        total_users=User.query.count(),
        total_workers=User.query.filter_by(role='worker').count(),
        total_employers=User.query.filter_by(role='employer').count(),
        total_jobs=JobPosting.query.count(),
        active_jobs=JobPosting.query.filter_by(is_active=True, is_filled=False).count(),
        completed_jobs=Match.query.filter_by(status='completed').count(),
        total_matches=Match.query.count(),
        total_reviews=Review.query.count(),
        role_filter=role_filter,
        search_query=search
    )

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', 'all')
    search = request.args.get('q', '').strip()

    q = User.query
    if role_filter in ['worker', 'employer']:
        q = q.filter_by(role=role_filter)
    if search:
        q = q.filter(User.full_name.ilike(f'%{search}%'))

    users = q.order_by(User.created_at.desc()).paginate(page=page, per_page=30, error_out=False)

    return render_template(
        'admin/users.html',
        users=users,
        role_filter=role_filter,
        search_query=search
    )

@app.route('/admin/user/<int:user_id>')
@login_required
@admin_required
def admin_view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('admin/view_user.html', user=user)

@app.route('/admin/user/<int:user_id>/verify')
@login_required
@admin_required
def admin_verify_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'worker' and user.worker_profile:
        user.worker_profile.id_verified = True
        user.is_verified = True
        db.session.commit()
        flash(f'{user.full_name} verified.', 'success')
    return redirect(url_for('admin_view_user', user_id=user_id))

@app.route('/admin/user/<int:user_id>/toggle-status')
@login_required
@admin_required
def admin_toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'{user.full_name} {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin_view_user', user_id=user_id))

@app.route('/admin/stats')
@login_required
@admin_required
def admin_stats():
    from sqlalchemy import func
    stats = {
        'total_users': User.query.count(),
        'total_workers': User.query.filter_by(role='worker').count(),
        'total_employers': User.query.filter_by(role='employer').count(),
        'verified_workers': WorkerProfile.query.filter_by(id_verified=True).count(),
        'total_jobs': JobPosting.query.count(),
        'active_jobs': JobPosting.query.filter_by(is_active=True, is_filled=False).count(),
        'completed_jobs': Match.query.filter_by(status='completed').count(),
        'total_matches': Match.query.count(),
        'total_reviews': Review.query.count(),
        'total_messages': Message.query.count(),
        'avg_rating': round(db.session.query(func.avg(WorkerProfile.rating_average)).scalar() or 0, 2),
        'recent_registrations': User.query.filter(User.created_at >= datetime.utcnow() - timedelta(days=30)).count(),
        'jobs_by_service': dict(
            db.session.query(JobPosting.service_type_needed, func.count(JobPosting.id))
            .group_by(JobPosting.service_type_needed).all()
        )
    }
    logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(50).all()
    return render_template('admin/stats.html', stats=stats, logs=logs)

# ----------------------------------------------------------------------
# API routes
# ----------------------------------------------------------------------
@app.route('/api/check-auth')
def api_check_auth():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'full_name': current_user.full_name,
                'role': current_user.role,
                'email': current_user.email
            }
        })
    return jsonify({'authenticated': False})

@app.route('/api/stats')
def api_stats():
    return jsonify({'success': True, 'stats': {
        'total_users': User.query.count(),
        'total_workers': User.query.filter_by(role='worker').count(),
        'total_employers': User.query.filter_by(role='employer').count(),
        'active_jobs': JobPosting.query.filter_by(is_active=True, is_filled=False).count(),
        'completed_jobs': Match.query.filter_by(status='completed').count()
    }})

@app.route('/api/jobs')
def api_jobs():
    q = JobPosting.query.filter_by(is_active=True, is_filled=False)

    # Regional filtering: if worker logged in, restrict to same country
    if current_user.is_authenticated and current_user.role == 'worker':
        worker = WorkerProfile.query.filter_by(user_id=current_user.id).first()
        if worker and worker.country:
            q = q.filter_by(country=worker.country)

    if request.args.get('service_type'):
        q = q.filter_by(service_type_needed=request.args.get('service_type'))
    if request.args.get('county'):
        q = q.filter_by(county=request.args.get('county'))
    if request.args.get('q'):
        q = q.filter(JobPosting.title.ilike(f"%{request.args.get('q')}%"))
    if request.args.get('sort') == 'high':
        q = q.order_by(JobPosting.offered_pay_rate.desc())
    else:
        q = q.order_by(JobPosting.created_at.desc())

    jobs = []
    for j in q.limit(50).all():
        emp = User.query.get(j.employer_id)
        jobs.append({
            'id': j.id,
            'title': j.title,
            'description': j.description[:150],
            'service_type_needed': j.service_type_needed,
            'service_name': j.service_type_needed.replace('_', ' ').title(),
            'location_name': j.location_name,
            'county': j.county or '',
            'country': j.country or 'Kenya',
            'offered_pay_rate': j.offered_pay_rate,
            'pay_period': j.pay_period,
            'time_ago': _time_ago(j.created_at),
            'employer_name': emp.full_name if emp else 'Anonymous',
            'application_count': Match.query.filter_by(job_posting_id=j.id, status='applied').count()
        })
    return jsonify({'success': True, 'jobs': jobs, 'total': len(jobs)})

@app.route('/api/workers')
def api_workers():
    q = WorkerProfile.query.filter_by(availability_status='available')

    # Regional filtering: if employer logged in, restrict to same country
    if current_user.is_authenticated and current_user.role == 'employer':
        emp = EmployerProfile.query.filter_by(user_id=current_user.id).first()
        if emp and emp.country:
            q = q.filter_by(country=emp.country)

    if request.args.get('service_type'):
        q = q.filter_by(service_type=request.args.get('service_type'))
    if request.args.get('county'):
        q = q.filter_by(county=request.args.get('county'))
    if request.args.get('q'):
        q = q.join(User).filter(User.full_name.ilike(f"%{request.args.get('q')}%"))
    if request.args.get('sort') == 'experience':
        q = q.order_by(WorkerProfile.experience_years.desc())
    else:
        q = q.order_by(WorkerProfile.rating_average.desc())

    workers = []
    for w in q.limit(50).all():
        u = User.query.get(w.user_id)
        workers.append({
            'id': w.id,
            'user_id': w.user_id,
            'full_name': u.full_name if u else 'Unknown',
            'service_type': w.service_type,
            'service_name': w.service_type.replace('_', ' ').title(),
            'experience_years': w.experience_years,
            'expected_pay_rate': w.expected_pay_rate,
            'pay_period': w.pay_period,
            'rating_average': round(w.rating_average, 1),
            'total_reviews': w.total_reviews,
            'locations': w.get_locations_list(),
            'county': w.county or '',
            'country': w.country or 'Kenya',
            'id_verified': w.id_verified,
            'selfie_path': w.selfie_path
        })
    return jsonify({'success': True, 'workers': workers, 'total': len(workers)})

@app.route('/api/employer/dashboard')
@login_required
@employer_required
def api_employer_dashboard():
    job_ids = [j.id for j in JobPosting.query.filter_by(employer_id=current_user.id).all()]
    return jsonify({'success': True, 'stats': {
        'active_jobs': JobPosting.query.filter_by(employer_id=current_user.id, is_active=True, is_filled=False).count(),
        'total_jobs': JobPosting.query.filter_by(employer_id=current_user.id).count(),
        'total_applications': Match.query.filter(
            Match.job_posting_id.in_(job_ids), Match.status == 'applied'
        ).count() if job_ids else 0,
        'total_hired': Match.query.filter(
            Match.job_posting_id.in_(job_ids), Match.status == 'hired'
        ).count() if job_ids else 0
    }})

@app.route('/api/worker/dashboard')
@login_required
@worker_required
def api_worker_dashboard():
    wp = WorkerProfile.query.filter_by(user_id=current_user.id).first()
    if not wp:
        return jsonify({'success': False})
    return jsonify({'success': True, 'stats': {
        'completed_jobs': Match.query.filter_by(worker_profile_id=wp.id, status='completed').count(),
        'pending_applications': Match.query.filter_by(worker_profile_id=wp.id, status='applied').count(),
        'active_matches': Match.query.filter(
            Match.worker_profile_id == wp.id,
            Match.status.in_(['contacted', 'interviewed', 'hired'])
        ).count(),
        'rating': round(wp.rating_average, 1),
        'total_reviews': wp.total_reviews,
        'profile_completion': (20 if wp.bio else 0) + (20 if wp.id_document_path else 0) +
                              (20 if wp.selfie_path else 0) + (20 if wp.get_locations_list() else 0) +
                              (20 if wp.id_verified else 0)
    }})

@app.route('/api/messages/<int:user_id>')
@login_required
def api_conversation(user_id):
    other = User.query.get(user_id)
    if not other:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).limit(100).all()

    unread = Message.query.filter_by(receiver_id=current_user.id, sender_id=user_id, is_read=False).all()
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()

    return jsonify({
        'success': True,
        'messages': [{
            'id': m.id,
            'content': m.content,
            'sender_id': m.sender_id,
            'is_mine': m.sender_id == current_user.id,
            'is_read': m.is_read,
            'created_at': m.created_at.strftime('%H:%M') if m.created_at else None
        } for m in messages],
        'other_user': {'id': other.id, 'full_name': other.full_name, 'role': other.role}
    })

@app.route('/api/messages/send', methods=['POST'])
@login_required
def api_send_message():
    data = request.get_json()
    if not data.get('receiver_id') or not data.get('content', '').strip():
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    msg = Message(
        sender_id=current_user.id,
        receiver_id=data['receiver_id'],
        content=data['content'].strip()
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': {
            'id': msg.id,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%H:%M')
        }
    })

@app.route('/api/notifications')
@login_required
def api_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify({
        'success': True,
        'unread_count': Notification.query.filter_by(user_id=current_user.id, is_read=False).count(),
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'time_ago': _time_ago(n.created_at)
        } for n in notifs]
    })

@app.route('/api/service-types')
def api_service_types():
    types = ['house_help', 'cleaner', 'plumber', 'electrician', 'gardener', 'painter',
             'carpenter', 'mason', 'welder', 'mechanic', 'driver', 'security_guard']
    return jsonify({
        'success': True,
        'services': [{
            'id': t,
            'name': t.replace('_', ' ').title(),
            'worker_count': WorkerProfile.query.filter_by(
                service_type=t, availability_status='available'
            ).count()
        } for t in types]
    })

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.get_json()
    print(f"Contact: {data.get('name')} - {data.get('email')} - {data.get('subject')}: {data.get('message')}")
    return jsonify({'success': True, 'message': 'Message received!'})

# ----------------------------------------------------------------------
# Seed data route
# ----------------------------------------------------------------------
@app.route('/seed-data')
def seed_data():
    if User.query.filter_by(role='worker').first():
        return jsonify({'success': False, 'message': 'Data already exists! Delete database first.'})

    workers = [
        ('John Kamau', 'john@test.com', 'plumber', 8, 15, 'Nairobi', 'Kenya'),
        ('Mary Wanjiku', 'mary@test.com', 'cleaner', 5, 10, 'Nairobi', 'Kenya'),
        ('Peter Omondi', 'peter@test.com', 'electrician', 12, 20, 'Nairobi', 'Kenya'),
        ('Jane Njeri', 'jane@test.com', 'house_help', 6, 12, 'Nairobi', 'Kenya'),
        ('David Muthoka', 'david@test.com', 'gardener', 4, 8, 'Nairobi', 'Kenya'),
        ('Grace Akinyi', 'grace@test.com', 'painter', 10, 18, 'Mombasa', 'Kenya'),
        ('Samuel Kiprotich', 'samuel@test.com', 'carpenter', 15, 25, 'Nakuru', 'Kenya'),
        ('Alice Chebet', 'alice@test.com', 'driver', 7, 10, 'Eldoret', 'Kenya')
    ]

    for name, email, svc, exp, rate, county, country in workers:
        u = User(email=email, phone=f'+2547{10000000 + len(name)}', full_name=name, role='worker')
        u.set_password('password123')
        db.session.add(u)
        db.session.flush()
        db.session.add(WorkerProfile(
            user_id=u.id,
            service_type=svc,
            experience_years=exp,
            expected_pay_rate=rate,
            pay_period='hourly',
            availability_status='available',
            preferred_locations=json.dumps(['Downtown', 'Westlands', 'Kilimani']),
            rating_average=round(3.5 + exp * 0.1, 1),
            total_reviews=exp * 2,
            completed_jobs=exp * 3,
            id_verified=True,
            country=country,
            county=county
        ))

    emp = User(email='employer@test.com', phone='+254700000001', full_name='ABC Company', role='employer')
    emp.set_password('password123')
    db.session.add(emp)
    db.session.flush()
    db.session.add(EmployerProfile(
        user_id=emp.id,
        company_name='ABC Company',
        city='Nairobi',
        country='Kenya',
        county='Nairobi'
    ))

    jobs = [
        ('Need Plumber for Kitchen', 'plumber', 'Westlands', 15, 'Nairobi', 'Kenya'),
        ('House Cleaner Needed', 'cleaner', 'Kilimani', 10, 'Nairobi', 'Kenya'),
        ('Electrician for Office', 'electrician', 'Downtown', 22, 'Nairobi', 'Kenya'),
        ('House Help for Family', 'house_help', 'Karen', 12, 'Nairobi', 'Kenya'),
        ('Gardener Large Compound', 'gardener', 'Lavington', 9, 'Nairobi', 'Kenya'),
        ('Interior Painter', 'painter', 'Parklands', 16, 'Nairobi', 'Kenya'),
        ('Carpenter Custom Wardrobe', 'carpenter', 'Kileleshwa', 20, 'Nairobi', 'Kenya'),
        ('Driver Family Transport', 'driver', 'Runda', 8, 'Nairobi', 'Kenya')
    ]

    for title, svc, loc, rate, county, country in jobs:
        db.session.add(JobPosting(
            employer_id=emp.id,
            title=title,
            description=f'Looking for reliable {svc} in {loc}. Must have experience and good references.',
            service_type_needed=svc,
            location_name=loc,
            offered_pay_rate=rate,
            is_active=True,
            country=country,
            county=county
        ))

    db.session.commit()
    return jsonify({'success': True, 'message': f'Seeded {len(workers)} workers and {len(jobs)} jobs! Use password123 to login.'})

# ----------------------------------------------------------------------
# Error handlers
# ----------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 THE WORKING MAN PLATFORM")
    print(f"📱 URL: http://localhost:5000")
    print(f"🔑 Admin: http://localhost:5000/admin")
    print(f"🌱 Seed: http://localhost:5000/seed-data")
    print("=" * 60)
    app.run(debug=True, port=5000, host='0.0.0.0')