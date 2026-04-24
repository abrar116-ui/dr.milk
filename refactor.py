import os
import re

def split_app():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Create directories
    os.makedirs('routes', exist_ok=True)
    os.makedirs('templates/errors', exist_ok=True)

    # We already have extensions.py and models.py
    # Let's extract User and Admin routes

    # Find User Routes (everything between @login_manager.user_loader and # --- Admin Routes ---)
    user_start = content.find('@login_manager.user_loader')
    admin_start = content.find('# --- Admin Routes ---')
    db_start = content.find('def create_db():')

    user_routes_block = content[user_start:admin_start]
    admin_routes_block = content[admin_start:db_start]
    seed_block = content[db_start:]

    # For user_routes.py, append the function wrapper
    user_routes_content = """from flask import render_template, request, session, redirect, url_for, jsonify, flash
from flask_login import login_user, login_required, logout_user, current_user
from models import User, LoginActivity, Product, ProductVariant, Order, OrderItem
from extensions import db, login_manager
from datetime import datetime, timedelta
from collections import defaultdict
import json

def register_user_routes(app):
"""
    # Replace @app.route with @app.route and indent all code by 4 spaces
    indented_user = "\n".join("    " + line if line.strip() else "" for line in user_routes_block.split("\n"))
    user_routes_content += indented_user
    
    # We also need to fix login_manager.user_loader inside register_user_routes, but wait, 
    # login_manager.user_loader doesn't need app, it needs login_manager which we import.
    # It can be at module level. Let's adjust the wrapper approach.
    
    user_routes_content2 = """from flask import render_template, request, session, redirect, url_for, jsonify, flash
from flask_login import login_user, login_required, logout_user, current_user
from models import User, LoginActivity, Product, ProductVariant, Order, OrderItem
from extensions import db, login_manager
from datetime import datetime, timedelta
from collections import defaultdict
import json

""" + user_routes_block.replace('@app.route', '@user_bp.route').replace('def load_user', 'def load_user')

    with open('routes/user_routes.py', 'w', encoding='utf-8') as f:
        f.write("from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, flash\n")
        f.write("from flask_login import login_user, login_required, logout_user, current_user\n")
        f.write("from models import User, LoginActivity, Product, ProductVariant, Order, OrderItem\n")
        f.write("from extensions import db, login_manager\n")
        f.write("from datetime import datetime, timedelta\n")
        f.write("from collections import defaultdict\n")
        f.write("import json\n\n")
        f.write("user_bp = Blueprint('user', __name__)\n\n")
        
        # Replace @app.route to @user_bp.route
        block_clean = user_routes_block.replace('@app.route', '@user_bp.route')
        f.write(block_clean)

    # Admin routes
    with open('routes/admin_routes.py', 'w', encoding='utf-8') as f:
        f.write("from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, flash\n")
        f.write("from flask_login import login_user, login_required, logout_user, current_user\n")
        f.write("from models import User, LoginActivity, Product, ProductVariant, Order, OrderItem\n")
        f.write("from extensions import db\n")
        f.write("from functools import wraps\n")
        f.write("from datetime import datetime, timedelta\n")
        f.write("from collections import defaultdict\n")
        f.write("import json\n")
        f.write("import os\n\n")
        f.write("admin_bp = Blueprint('admin', __name__)\n\n")
        f.write('''def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

''')
        block_clean = admin_routes_block.replace('@app.route', '@admin_bp.route')
        # Wait, inside admin_routes, they use `app.config['UPLOAD_FOLDER']`. Let's import `current_app`.
        f.write("from flask import current_app\n")
        block_clean = block_clean.replace("app.config['UPLOAD_FOLDER']", "current_app.config['UPLOAD_FOLDER']")
        f.write(block_clean)

    # Now recreate app.py
    app_py_content = """import os
from flask import Flask, render_template
from extensions import db, login_manager
from models import User, Product, ProductVariant
from routes.user_routes import user_bp
from routes.admin_routes import admin_bp
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dr_milk_premium_secret_key')

# Image Upload Configuration
UPLOAD_FOLDER = 'static/images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///drmilk.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'user.login'

# Register Blueprints
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

""" + seed_block + """
"""
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(app_py_content)

if __name__ == '__main__':
    split_app()
    print("Code separation completed.")
