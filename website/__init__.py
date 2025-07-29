from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import os

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__, 
                static_folder=os.path.abspath('website/static'), 
                static_url_path='/static')
    app.config['SECRET_KEY'] = 'freshness detection'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = os.path.abspath('website/static/uploads')
    app.config['RESULT_FOLDER'] = os.path.abspath('website/static/results')
    app.config['SAVED_RESULTS_FOLDER'] = os.path.abspath('website/static/saved_results')
    db.init_app(app)
    
    from .views import views
    from .auth import auth
    from .app import app as app_blueprint
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(app_blueprint, url_prefix='/')
    
    # Configure error handling
    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({"error": "Not found", "message": str(e)}), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
    
    from .models import User
    
    create_database(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app

def create_database(app):
    with app.app_context():
        if not path.exists('website/' + DB_NAME):
            db.create_all()
            print('Created Database!')
    

