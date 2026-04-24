import os
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

def create_db():
    with app.app_context():
        db.create_all()
        if not Product.query.first():
            seed_data()

def seed_data():
    initial_products = [
        {
            'name': 'A2 Cow Milk',
            'description': 'Pure A2 milk from our own cow farm',
            'benefits': ['High in A2 Protein', 'Easy to Digest', 'Rich in Nutrients', 'Fresh Daily'],
            'image': 'a2-cow-milk.jpg',
            'prices': {'500ml': (60, 0.5), '1ltr': (110, 1.0)},
            'category': 'Milk'
        },
        {
            'name': 'Buffalo Milk Gold',
            'description': 'Creamy and nutrient-rich buffalo milk',
            'benefits': ['High Calcium', 'Rich Taste', 'Creamier Texture', 'Premium Quality'],
            'image': 'buffalo-milk-gold.jpg',
            'prices': {'500ml': (70, 0.5), '1ltr': (130, 1.0)},
            'category': 'Milk'
        },
        {
            'name': 'Buffalo Milk Gold+',
            'description': 'Enhanced buffalo milk with added benefits',
            'benefits': ['Extra Creaminess', 'Higher Fat Content', 'Premium Grade', 'Best for Ghee'],
            'image': 'buffalo-milk-goldplus.jpg',
            'prices': {'500ml': (80, 0.5), '1ltr': (150, 1.0)},
            'category': 'Milk'
        },
        {
            'name': 'Cow Ghee',
            'description': 'Traditional Bilona ghee from cow milk',
            'benefits': ['Pure Bilona Method', 'High Nutritional Value', 'Golden Color', 'Traditional Recipe'],
            'image': 'cow-ghee.svg',
            'prices': {'250ml': (300, 0.25), '500ml': (550, 0.5)},
            'category': 'Ghee'
        },
        {
            'name': 'Buffalo Ghee',
            'description': 'Premium ghee made from buffalo milk',
            'benefits': ['Rich Aroma', 'Authentic Taste', 'Bilona Processed', 'Long Shelf Life'],
            'image': 'buffalo-ghee.svg',
            'prices': {'250ml': (320, 0.25), '500ml': (600, 0.5)},
            'category': 'Ghee'
        },
        {
            'name': 'Buttermilk',
            'description': 'Fresh, probiotic-rich buttermilk',
            'benefits': ['Aids Digestion', 'Probiotic Rich', 'Low Calorie', 'Refreshing Taste'],
            'image': 'buttermilk.svg',
            'prices': {'500ml': (40, 0.5), '1ltr': (75, 1.0)},
            'category': 'Dairy'
        },
        {
            'name': 'Butter',
            'description': 'Creamy fresh butter churned daily',
            'benefits': ['All-Natural Ingredients', 'Premium Quality', 'Fresh Churned', 'Rich Flavor'],
            'image': 'butter.svg',
            'prices': {'250ml': (200, 0.25), '500ml': (380, 0.5)},
            'category': 'Dairy'
        },
        {
            'name': 'Paneer',
            'description': 'Fresh cottage cheese made from pure milk',
            'benefits': ['High Protein', 'Fresh Daily', 'Soft Texture', 'Versatile Use'],
            'image': 'paneer.svg',
            'prices': {'500g': (250, 0.5), '1kg': (480, 1.0)},
            'category': 'Dairy'
        }
    ]

    for p_data in initial_products:
        product = Product(
            name=p_data['name'],
            description=p_data['description'],
            benefits=p_data['benefits'],
            image=p_data['image'],
            category=p_data['category']
        )
        db.session.add(product)
        db.session.flush()
        
        for size, (price, liter_val) in p_data['prices'].items():
            variant = ProductVariant(product_id=product.id, size=size, price=price, liter_value=liter_val)
            db.session.add(variant)
    
    # Create a default admin user
    admin = User(username='admin', role='admin', email='admin@drmilk.in')
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create a test customer
    user = User(
        username='testdealer', 
        role='customer', 
        email='dealer@drmilk.in',
        phone='7359238846',
        address='Bhavnagar, Gujarat',
        society='Shanti Sadan',
        block='A',
        flat_number='404'
    )
    user.set_password('milk123')
    db.session.add(user)
    
    db.session.commit()

if __name__ == '__main__':
    create_db()
    app.run(debug=True)

