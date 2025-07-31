from flask import Flask, render_template, redirect, url_for, flash, request, session, send_from_directory
from forms import RegisterForm, LoginForm, JobForm
from models import db, User, Job, Application, SavedJob
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from datetime import date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobportal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload folders
app.config['RESUME_FOLDER'] = os.path.join('static', 'resumes')
os.makedirs(app.config['RESUME_FOLDER'], exist_ok=True)

app.config['PROFILE_IMAGE_FOLDER'] = os.path.join('static', 'profile_images')
os.makedirs(app.config['PROFILE_IMAGE_FOLDER'], exist_ok=True)

app.config['UPLOAD_FOLDER'] = app.config['RESUME_FOLDER']

# Initialize DB and Migration
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    role = request.args.get('role', '').lower()
    location = request.args.get('location', '').lower()

    today = date.today()
    jobs = Job.query.filter((Job.expiration_date == None) | (Job.expiration_date >= today))

    if role:
        jobs = jobs.filter(Job.title.ilike(f'%{role}%'))
    if location:
        jobs = jobs.filter(Job.location.ilike(f'%{location}%'))

    jobs = jobs.all()
    return render_template('index.html', jobs=jobs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pwd = generate_password_hash(form.password.data)
        user = User(username=form.username.data, role=form.role.data, password=hashed_pwd)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard') if user.role == 'employer' else url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        user.email = request.form.get('email')
        user.qualification = request.form.get('qualification')
        user.projects = request.form.get('projects')
        user.linkedin = request.form.get('linkedin')
        user.cgpa = request.form.get('cgpa')

        profile_image = request.files.get('profile_image')
        if profile_image and profile_image.filename:
            filename = secure_filename(profile_image.filename)
            filepath = os.path.join(app.config['PROFILE_IMAGE_FOLDER'], filename)
            profile_image.save(filepath)
            user.profile_image = filename

        resume_file = request.files.get('resume')
        if resume_file and resume_file.filename:
            filename = secure_filename(resume_file.filename)
            filepath = os.path.join(app.config['RESUME_FOLDER'], filename)
            resume_file.save(filepath)
            user.resume = filename

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/resume/<filename>')
def download_resume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role')
    user_id = session['user_id']
    if role == 'employer':
        jobs = Job.query.filter_by(posted_by=user_id).all()
        return render_template('dashboard.html', role=role, jobs=jobs, current_date=date.today())
    else:
        applications = Application.query.filter_by(seeker_id=user_id).all()
        saved_jobs = SavedJob.query.filter_by(seeker_id=user_id).all()
        return render_template('dashboard.html', role=role, applications=applications, saved_jobs=saved_jobs, current_date=date.today())

@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if session.get('role') != 'employer':
        return redirect(url_for('dashboard'))
    form = JobForm()
    if form.validate_on_submit():
        job = Job(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            company=form.company.data,
            salary=form.salary.data,
            expiration_date=form.expiration_date.data,
            posted_by=session['user_id']
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('post_job.html', form=form)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    is_expired = job.expiration_date and job.expiration_date < date.today()

    already_applied = False
    if 'user_id' in session and session.get('role') == 'seeker':
        already_applied = Application.query.filter_by(
            job_id=job.id, seeker_id=session['user_id']).first() is not None

    return render_template('job_detail.html', job=job, already_applied=already_applied, is_expired=is_expired, current_date=date.today())

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply_job(job_id):
    if 'user_id' not in session or session.get('role') != 'seeker':
        flash('Only job seekers can apply!', 'warning')
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)
    user = User.query.get(session['user_id'])

    if Application.query.filter_by(job_id=job.id, seeker_id=user.id).first():
        flash('You have already applied for this job.', 'info')
        return redirect(url_for('job_detail', job_id=job.id))

    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        location = request.form.get('location')
        resume = request.files.get('resume')

        filename = None
        if resume and resume.filename != '':
            filename = secure_filename(resume.filename)
            resume.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.resume = filename
            db.session.commit()
        elif user.resume:
            filename = user.resume

        application = Application(
            job_id=job.id,
            seeker_id=user.id,
            email=email,
            phone=phone,
            location=location,
            resume_filename=filename
        )
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('job_detail', job_id=job.id))

    return render_template('apply_form.html', job=job, user=user)

@app.route('/save/<int:job_id>')
def save_job(job_id):
    if 'user_id' not in session or session.get('role') != 'seeker':
        flash('Only job seekers can save jobs!', 'warning')
        return redirect(url_for('login'))

    if SavedJob.query.filter_by(job_id=job_id, seeker_id=session['user_id']).first():
        flash('Job already saved.', 'info')
        return redirect(url_for('index'))

    save = SavedJob(job_id=job_id, seeker_id=session['user_id'])
    db.session.add(save)
    db.session.commit()
    flash('Job saved successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/saved-jobs')
def view_saved_jobs():
    if 'user_id' not in session or session.get('role') != 'seeker':
        flash('Only job seekers can view saved jobs.', 'warning')
        return redirect(url_for('login'))

    saved = SavedJob.query.filter_by(seeker_id=session['user_id']).all()
    jobs = [Job.query.get(s.job_id) for s in saved if Job.query.get(s.job_id)]
    return render_template('saved_jobs.html', jobs=jobs)

@app.route('/search')
def search_jobs():
    keyword = request.args.get('keyword', '').lower()
    location = request.args.get('location', '').lower()
    company = request.args.get('company', '').lower()
    min_salary = request.args.get('min_salary', type=int)

    query = Job.query
    if keyword:
        query = query.filter(Job.title.ilike(f"%{keyword}%") | Job.description.ilike(f"%{keyword}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if company:
        query = query.filter(Job.company.ilike(f"%{company}%"))
    if min_salary is not None:
        query = query.filter(Job.salary >= min_salary)

    today = date.today()
    jobs = query.filter((Job.expiration_date == None) | (Job.expiration_date >= today)).all()

    return render_template('search_results.html', jobs=jobs)

@app.route('/applications/<int:job_id>')
def view_applications(job_id):
    if 'user_id' not in session or session.get('role') != 'employer':
        flash('Only employers can view applications!', 'warning')
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)

    if job.posted_by != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    applications = Application.query.filter_by(job_id=job.id).all()
    return render_template('applications.html', job=job, applications=applications)

@app.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'user_id' not in session or session.get('role') != 'employer':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)
    if job.posted_by != session['user_id']:
        flash("You can only edit your own jobs.", "danger")
        return redirect(url_for('dashboard'))

    form = JobForm(obj=job)

    if form.validate_on_submit():
        job.title = form.title.data
        job.description = form.description.data
        job.location = form.location.data
        job.company = form.company.data
        job.salary = form.salary.data
        job.expiration_date = form.expiration_date.data
        db.session.commit()

        flash("Job updated successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('edit_job.html', form=form, job=job)

@app.route('/delete-job/<int:job_id>')
def delete_job(job_id):
    if 'user_id' not in session or session.get('role') != 'employer':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)
    if job.posted_by != session['user_id']:
        flash("You can only delete your own jobs.", "danger")
        return redirect(url_for('dashboard'))

    Application.query.filter_by(job_id=job.id).delete()
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin access only.', 'danger')
        return redirect(url_for('login'))

    users = User.query.all()
    jobs = Job.query.all()
    applications = Application.query.all()

    return render_template('admin.html', users=users, jobs=jobs, applications=applications, current_date=date.today())

# ✅ Final Fallback for Render: Create DB if not exists
if __name__ == "__main__":
    with app.app_context():
        if not os.path.exists(os.path.join("instance", "jobportal.db")):
            db.create_all()
            print("✅ Database created using db.create_all()")
    app.run(debug=True)
