<<<<<<< HEAD
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

=======
import secrets
import os
import json
import csv
import sqlalchemy
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'dr_milk_premium_secret_key'

# Image Upload Configuration
UPLOAD_FOLDER = 'static/images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///drmilk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='customer') # 'admin' or 'customer'
    
    # New Profile Fields
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    society = db.Column(db.String(100))
    block = db.Column(db.String(50))
    flat_number = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LoginActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(20)) # 'login' or 'logout'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('activities', lazy=True))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    category = db.Column(db.String(50))
    benefits = db.Column(db.JSON)
    variants = db.relationship('ProductVariant', backref='product', lazy=True)

class ProductVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    size = db.Column(db.String(50), nullable=False) # e.g., '1ltr', '500ml'
    price = db.Column(db.Float, nullable=False)
    liter_value = db.Column(db.Float) # New: store actual liter value (e.g. 1.0 or 0.5)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    total_amount = db.Column(db.Float, nullable=False)
    total_liters = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Pending')
    delivery_time = db.Column(db.String(20)) # 'Morning', 'Evening'
    delivery_days = db.Column(db.JSON) # ['Monday', 'Tuesday'...]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_id = db.Column(db.String(50), unique=True)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product')
    size = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    liter_total = db.Column(db.Float) # quantity * variant.liter_value

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    category = request.args.get('category')
    if category:
        products_query = Product.query.filter_by(category=category).all()
    else:
        products_query = Product.query.all()
    
    # Format products for template to match previous structure
    formatted_products = []
    for p in products_query:
        prices = {v.size: v.price for v in p.variants}
        formatted_products.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'benefits': p.benefits,
            'image': p.image,
            'prices': prices
        })

    # Personal Greeting Logic
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good Morning"
    elif 12 <= hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    features = [
        {'title': '100% Pure & Natural', 'description': 'No additives, preservatives, or chemicals', 'icon': '✓'},
        {'title': 'Own Farm Production', 'description': 'Complete control over quality from farm to home', 'icon': '🌾'},
        {'title': 'Glass Bottle Packaging', 'description': 'Eco-friendly and maintains milk freshness', 'icon': '🔷'},
        {'title': 'Daily Fresh Delivery', 'description': 'Delivered fresh to your doorstep every morning', 'icon': '🚚'},
        {'title': 'Certified & Tested', 'description': 'Food safety certified with rigorous quality testing', 'icon': '✅'},
        {'title': 'Pasteurization', 'description': 'Heat-treated for safety while maintaining nutritional value', 'icon': '🔥'},
        {'title': 'Sustainable & Eco Friendly', 'description': 'Environment-conscious farming and packaging', 'icon': '🌱'}
    ]

    return render_template('index.html', 
                         products=formatted_products, 
                         features=features, 
                         greeting=greeting)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            # Track Login
            activity = LoginActivity(user_id=user.id, activity_type='login')
            db.session.add(activity)
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        if not email: email = None
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')

        if User.query.filter_by(username=username).first():
            return render_template('signup.html', error='Username already exists')

        new_user = User(
            username=username, 
            email=email,
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            society=request.form.get('society'),
            block=request.form.get('block'),
            flat_number=request.form.get('flat_number')
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    activity = LoginActivity(user_id=current_user.id, activity_type='logout')
    db.session.add(activity)
    db.session.commit()
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.get_json()
    product_id = int(data.get('product_id'))
    size = data.get('size')
    quantity = int(data.get('quantity', 1))
    
    meta = data.get('meta')
    
    if 'cart' not in session:
        session['cart'] = []
    
    # If it's a subscription (has meta), always add as a new item to keep preferences separate
    # Otherwise, merge identical items
    if meta:
        session['cart'].append({'product_id': product_id, 'size': size, 'quantity': quantity, 'meta': meta})
    else:
        cart_item = next((item for item in session['cart'] if item['product_id'] == product_id and item['size'] == size and 'meta' not in item), None)
        if cart_item:
            cart_item['quantity'] += quantity
        else:
            session['cart'].append({'product_id': product_id, 'size': size, 'quantity': quantity})
    
    session.modified = True
    return jsonify({'success': True, 'message': 'Added to cart'})

@app.route('/remove_from_cart/<int:product_id>/<size>', methods=['POST'])
@login_required
def remove_from_cart(product_id, size):
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if not (item['product_id'] == product_id and item['size'] == size)]
        session.modified = True
    return jsonify({'success': True, 'message': 'Item removed'})

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if not session.get('cart'):
        flash('Your cart is empty', 'warning')
        return redirect(url_for('home'))
        
    cart_items = session.get('cart', [])
    total_amount = 0.0
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            variant = ProductVariant.query.filter_by(product_id=product.id, size=item['size']).first()
            if variant:
                total_amount += variant.price * item['quantity']

    if request.method == 'POST':
        total_amount = 0.0
        total_liters = 0.0
        
        # In a real app, generate a unique order_id
        import uuid
        order_id = str(uuid.uuid4())[:8].upper()
        
        # Get delivery days from form
        days_json = request.form.get('delivery_days', '[]')
        try:
            days = json.loads(days_json)
        except:
            days = []
            
        # Create Order
        new_order = Order(
            user_id=current_user.id,
            total_amount=0, # temp
            total_liters=0, # temp
            status='Pending',
            delivery_time=request.form.get('delivery_time', 'Morning'),
            delivery_days=days,
            order_id=order_id
        )
        
        db.session.add(new_order)
        db.session.flush()
        
        for item in cart_items:
            product = Product.query.get(item['product_id'])
            variant = ProductVariant.query.filter_by(product_id=product.id, size=item['size']).first()
            if variant:
                item_total = variant.price * item['quantity']
                total_amount += item_total
                
                # Liters tracking
                liters = (variant.liter_value or 0) * item['quantity']
                total_liters += liters
                
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    size=item['size'],
                    quantity=item['quantity'],
                    price=variant.price,
                    liter_total=liters
                )
                db.session.add(order_item)
                
        new_order.total_amount = total_amount
        new_order.total_liters = total_liters
        
        db.session.commit()
        session.pop('cart', None)
        flash('Order placed successfully!', 'success')
        return redirect(url_for('user_orders'))
        
    return render_template('checkout.html', total_amount=total_amount)

@app.route('/cart')
@login_required
def view_cart():
    cart_items = session.get('cart', [])
    cart_details = []
    total_amount = 0.0
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            variant = ProductVariant.query.filter_by(product_id=product.id, size=item['size']).first()
            if variant:
                item_total = variant.price * item['quantity']
                total_amount += item_total
                cart_details.append({
                    'product': product,
                    'size': item['size'],
                    'quantity': item['quantity'],
                    'price': variant.price,
                    'item_total': item_total
                })
    return render_template('cart.html', cart_details=cart_details, total_amount=total_amount)

@app.route('/orders')
@login_required
def user_orders():
    all_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    # Calculate today and tomorrow days (e.g., 'Mon', 'Tue')
    today_day = datetime.now().strftime('%a')
    tomorrow_day = (datetime.now() + timedelta(days=1)).strftime('%a')
    
    today_orders = [o for o in all_orders if today_day in (o.delivery_days or [])]
    tomorrow_orders = [o for o in all_orders if tomorrow_day in (o.delivery_days or [])]
    
    # Filter all_orders to not include today/tomorrow deliveries (pure history)
    history_orders = [o for o in all_orders if o not in today_orders and o not in tomorrow_orders]
    
    # Group history orders by date
    grouped_history = defaultdict(list)
    for order in history_orders:
        date_key = order.created_at.strftime('%Y-%m-%d')
        grouped_history[date_key].append(order)
    
    # Create sorted list of (formatted_date, orders)
    sorted_history_keys = sorted(grouped_history.keys(), reverse=True)
    display_history = []
    for d_key in sorted_history_keys:
        dt = datetime.strptime(d_key, '%Y-%m-%d')
        display_history.append({
            'date': dt.strftime('%A, %d %B %Y'),
            'orders': grouped_history[d_key]
        })
    
    return render_template('orders.html', 
                         today_orders=today_orders, 
                         tomorrow_orders=tomorrow_orders, 
                         display_history=display_history)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.phone = request.form.get('phone')
        current_user.address = request.form.get('address')
        current_user.society = request.form.get('society')
        current_user.block = request.form.get('block')
        current_user.flat_number = request.form.get('flat_number')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Calculate Monthly Subscription Stats
    now = datetime.now()
    month_name = now.strftime('%B')
    year = now.year
    month = now.month
    
    # Get all active orders for this user this month (plus past months if they are ongoing)
    active_orders = Order.query.filter(
        Order.user_id == current_user.id,
        Order.status != 'Cancelled'
    ).all()
    
    import calendar
    num_days = calendar.monthrange(year, month)[1]
    
    month_sheet = []
    delivery_days_count = 0
    unique_products = set()
    total_month_spent = 0.0
    
    for day_num in range(1, num_days + 1):
        date_obj = datetime(year, month, day_num)
        day_name = date_obj.strftime('%a') # Mon, Tue...
        
        # Check which orders apply to this day
        day_deliveries = []
        for order in active_orders:
            if order.delivery_days and day_name in order.delivery_days:
                for item in order.items:
                    day_deliveries.append({
                        'product': item.product.name if item.product else "Unknown",
                        'size': item.size,
                        'quantity': item.quantity,
                        'amount': item.price * item.quantity
                    })
                    unique_products.add(item.product.name if item.product else "Unknown")
                    total_month_spent += (item.price * item.quantity)
        
        if day_deliveries:
            delivery_days_count += 1
            month_sheet.append({
                'date': date_obj.strftime('%d %b'),
                'day': date_obj.strftime('%A'),
                'deliveries': day_deliveries,
                'is_past': date_obj.date() < now.date(),
                'is_today': date_obj.date() == now.date()
            })

    stats = {
        'month_name': month_name,
        'total_delivery_days': delivery_days_count,
        'ordered_products': list(unique_products),
        'total_spent': total_month_spent,
        'month_sheet': month_sheet
    }
    
    return render_template('profile.html', user=current_user, stats=stats)

# --- Admin Routes ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, role='admin').first()
        if user and user.check_password(password):
            login_user(user)
            # Track Login
            activity = LoginActivity(user_id=user.id, activity_type='login')
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin/login.html', error='Invalid admin credentials')
    
    return render_template('admin/login.html')

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    from sqlalchemy import func
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime('%Y-%m-%d')
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    # Analytics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Login stats
    logins_today = LoginActivity.query.filter(
        func.date(LoginActivity.timestamp) == today_str,
        LoginActivity.activity_type == 'login'
    ).count()
    
    logouts_today = LoginActivity.query.filter(
        func.date(LoginActivity.timestamp) == today_str,
        LoginActivity.activity_type == 'logout'
    ).count()
    
    # Order stats
    orders_today = Order.query.filter(func.date(Order.created_at) == today_str).count()
    orders_yesterday = Order.query.filter(func.date(Order.created_at) == yesterday_str).count()
    
    # Milk stats (liters)
    milk_today = db.session.query(func.sum(Order.total_liters)).filter(
        func.date(Order.created_at) == today_str
    ).scalar() or 0
    
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'logins_today': logins_today,
        'logouts_today': logouts_today,
        'orders_today': orders_today,
        'orders_yesterday': orders_yesterday,
        'milk_today': round(milk_today, 2),
        'total_revenue': round(total_revenue, 2),
        'now_text': datetime.now().strftime('%B %d, %Y')
    }
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Charts Data (Dummy/Aggregated for Chart.js)
    # In a real app, you'd fetch real time-series data here.
    chart_data = {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'milk_delivery': [45, 52, 48, 61, 55, 67, 72],
        'orders': [10, 12, 11, 15, 13, 18, 20]
    }

    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders, chart_data=chart_data)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>')
@login_required
@admin_required
def admin_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    # Calculate subscription months
    delta = datetime.now() - user.created_at
    months = delta.days // 30
    return render_template('admin/user_profile.html', user=user, sub_months=months)

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['POST'])
@login_required
@admin_required
def admin_add_product():
    name = request.form.get('name')
    category = request.form.get('category')
    description = request.form.get('description')
    
    # Handle Image Upload or URL
    image = request.form.get('image')
    image_file = request.files.get('image_file')
    
    if image_file and getattr(image_file, 'filename', ''):
        import werkzeug.utils
        filename = werkzeug.utils.secure_filename(getattr(image_file, 'filename'))
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        image = filename

    # Create product
    new_product = Product(
        name=name,
        category=category,
        description=description,
        image=image,
        benefits=[]
    )
    db.session.add(new_product)
    db.session.flush()

    # Add pricing variants
    size1 = request.form.get('size1')
    price1 = request.form.get('price1')
    if size1 and price1:
        v1 = ProductVariant(product_id=new_product.id, size=size1, price=float(price1))
        db.session.add(v1)
        
    size2 = request.form.get('size2')
    price2 = request.form.get('price2')
    if size2 and price2:
        v2 = ProductVariant(product_id=new_product.id, size=size2, price=float(price2))
        db.session.add(v2)

    db.session.commit()
    flash('Product added successfully', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/delete/<int:id>')
@login_required
@admin_required
def admin_delete_product(id):
    product = Product.query.get_or_404(id)
    # Delete variants first to maintain relational integrity
    ProductVariant.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    # Group orders by date
    grouped = defaultdict(list)
    for order in orders:
        date_key = order.created_at.strftime('%Y-%m-%d')
        grouped[date_key].append(order)
    
    # Create a sorted list of (formatted_date, orders)
    sorted_date_keys = sorted(grouped.keys(), reverse=True)
    display_orders = []
    
    for d_key in sorted_date_keys:
        # Create a datetime object to format it nicely
        dt = datetime.strptime(d_key, '%Y-%m-%d')
        formatted_date = dt.strftime('%A, %d %B %Y')
        display_orders.append({
            'date': formatted_date,
            'orders': grouped[d_key]
        })
    
    return render_template('admin/orders.html', display_orders=display_orders)

@app.route('/admin/orders/update/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form.get('status')
    db.session.commit()
    return redirect(url_for('admin_orders'))

@app.route('/admin/orders/delete/<int:id>')
@login_required
@admin_required
def admin_delete_order(id):
    order = Order.query.get_or_404(id)
    # Also delete associated items
    OrderItem.query.filter_by(order_id=order.id).delete()
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/export/<report_type>')
@login_required
@admin_required
def export_report(report_type):
    import csv
    from io import StringIO
    from flask import make_response

    si = StringIO()
    cw = csv.writer(si)
    
    if report_type == 'users':
        cw.writerow(['ID', 'Username', 'Email', 'Phone', 'Address', 'Status', 'Registered At'])
        users = User.query.all()
        for u in users:
            cw.writerow([u.id, u.username, u.email, u.phone, u.address, u.is_active, u.created_at])
    elif report_type == 'orders':
        cw.writerow(['Order ID', 'User', 'Amount', 'Liters', 'Status', 'Date'])
        orders = Order.query.all()
        for o in orders:
            cw.writerow([o.order_id, o.user.username, o.total_amount, o.total_liters, o.status, o.created_at])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={report_type}_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

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
>>>>>>> 674038acaea1553ff7758abf94159b647b581115
