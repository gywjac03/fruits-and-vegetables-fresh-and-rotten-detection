from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from . import db
import os
import secrets
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login(): 
    if request.method == 'POST':
        userName = request.form.get('userName')  
        password = request.form.get('password')
        
        user = User.query.filter_by(userName=userName).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Login Successful', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect Password', category='error')
        else: 
            flash('Username does not exist', category='error')
    
    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout(): 
    logout_user()
    return redirect(url_for('views.home'))

@auth.route('/update-profile-pic', methods=['POST'])
@login_required
def update_profile_pic():
    if 'profile_pic' not in request.files:
        flash('No file selected', category='error')
        return redirect(url_for('views.profile'))
    
    profile_pic = request.files['profile_pic']
    
    if profile_pic.filename == '':
        flash('No file selected', category='error')
        return redirect(url_for('views.profile'))
    
    # Check if the file has an allowed extension
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    file_ext = profile_pic.filename.rsplit('.', 1)[1].lower() if '.' in profile_pic.filename else ''
    
    if file_ext not in allowed_extensions:
        flash('Only image files (JPG, PNG, GIF) are allowed', category='error')
        return redirect(url_for('views.profile'))
    
    # Create a secure filename with a random token to prevent filename collisions
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(profile_pic.filename)
    new_filename = random_hex + file_ext
    
    # Save the file
    upload_folder = os.path.join('website', 'static', 'uploads', 'profile_pics')
    file_path = os.path.join(upload_folder, new_filename)
    
    # Delete old profile pic if it's not the default
    if current_user.profile_pic != 'default.jpg':
        try:
            old_file_path = os.path.join(upload_folder, current_user.profile_pic)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        except Exception as e:
            # Just log the error and continue
            print(f"Error removing old profile pic: {e}")
    
    profile_pic.save(file_path)
    
    # Update the user's profile_pic field in the database
    current_user.profile_pic = new_filename
    db.session.commit()
    
    flash('Profile picture updated successfully!', category='success')
    return redirect(url_for('views.profile'))

@auth.route('/register', methods=['GET', 'POST'])
def register(): 
    if request.method =='POST':
        userName = request.form.get('userName')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        user = User.query.filter_by(userName=userName).first()
        if user:
            flash('User already exist', category='error')
        elif len(userName) < 2:
            flash('Username must be more than 2 characters', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif password1 != password2:
            flash('Password is incorrect', category='error')
        elif len(password1) < 8:
            flash('Password must be more than 8 characters', category='error')
        else:
            #Add user to database
            new_user = User(userName=userName, 
                            email=email, 
                            password=generate_password_hash(password1, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account successfully registered!', category='success')
            return redirect(url_for('views.home'))
       
    return render_template("register.html", user=current_user)



