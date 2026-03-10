
from app import app, db, User, Product, ProductVariant, Order, OrderItem, LoginActivity, seed_data
import os

with app.app_context():
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    # Get the actual database file path
    # For sqlite:///drmilk.db it should be in the instance or root
    db_path = os.path.join(app.instance_path, 'drmilk.db')
    print(f"Checking for DB at {db_path}")
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed existing DB")
    
    db.create_all()
    print("Created all tables")
    seed_data()
    print("Data seeded")
