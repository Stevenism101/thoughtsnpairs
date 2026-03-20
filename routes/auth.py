from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        error = None
        if not username or len(username) < 3:
            error = 'Username must be at least 3 characters.'
        elif User.query.filter_by(username=username).first():
            error = 'That username is taken.'
        elif not email or '@' not in email:
            error = 'Enter a valid email.'
        elif User.query.filter_by(email=email).first():
            error = 'An account with that email already exists.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'

        if error:
            flash(error, 'error')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            session['show_first_pairing_prompt'] = True
            return redirect(url_for('auth.first_pairing'))

    return render_template('auth/register.html')

@auth_bp.route('/first-pairing')
@login_required
def first_pairing():
    return render_template('auth/first_pairing.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Wrong username or password.', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
