from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

def ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='customer') # 'admin' or 'customer'
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    society = db.Column(db.String(100))
    block = db.Column(db.String(50))
    flat_number = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=ist_now, index=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LoginActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    activity_type = db.Column(db.String(20)) # 'login' or 'logout'
    timestamp = db.Column(db.DateTime, default=ist_now, index=True)
    user = db.relationship('User', backref=db.backref('activities', lazy=True))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    category = db.Column(db.String(50), index=True)
    benefits = db.Column(db.JSON)
    variants = db.relationship('ProductVariant', backref='product', lazy=True)

class ProductVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    size = db.Column(db.String(50), nullable=False) # e.g., '1ltr', '500ml'
    price = db.Column(db.Float, nullable=False)
    liter_value = db.Column(db.Float)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    total_amount = db.Column(db.Float, nullable=False)
    total_liters = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Pending', index=True)
    delivery_time = db.Column(db.String(20)) # 'Morning', 'Evening'
    delivery_days = db.Column(db.JSON) # ['Monday', 'Tuesday'...]
    is_subscription = db.Column(db.Boolean, default=False)
    subscription_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=ist_now, index=True)
    order_id = db.Column(db.String(50), unique=True, index=True)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product')
    size = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    liter_total = db.Column(db.Float)
