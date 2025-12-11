from backend.extensions import db, login_manager, csrf, migrate
from backend.config import Config
from flask import Flask, redirect, url_for, render_template


def create_app(*args,**kwargs):
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Import blueprints
    from backend.routes_auth import auth_bp
    from backend.routes import dashboard_bp
    from backend.routes_marketplace import marketplace_bp
    from backend.routes_community import community_bp
    from backend.routes_messaging import messaging_bp
    from backend.routes_profile import profile_bp
    from backend.routes_notifications import notifications_bp

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(messaging_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(notifications_bp)  # <- register notifications blueprint

    # Context processor to inject models into templates globally
    @app.context_processor
    def inject_models():
        from backend.models import Notification, Post, Listing
        return dict(Notification=Notification, Post=Post, Listing=Listing)

    # Home redirect
    @app.route('/')
    def home():
        from flask_login import current_user
        
        return render_template('landing.html')

    return app
