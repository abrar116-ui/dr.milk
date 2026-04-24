import os
import re

def update_templates():
    user_endpoints = ['home', 'login', 'signup', 'logout', 'add_to_cart', 'remove_from_cart', 'checkout', 'view_cart', 'user_orders', 'profile']
    admin_endpoints = ['admin_login', 'admin_dashboard', 'admin_users', 'admin_user_profile', 'admin_products', 'admin_add_product', 'admin_delete_product', 'admin_orders', 'update_order_status', 'admin_delete_order', 'export_report', 'admin_quick_delivery']

    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace user routes
                for ep in user_endpoints:
                    content = content.replace(f"url_for('{ep}'", f"url_for('user.{ep}'")
                    content = content.replace(f'url_for("{ep}"', f'url_for("user.{ep}"')
                
                # Replace admin routes
                for ep in admin_endpoints:
                    content = content.replace(f"url_for('{ep}'", f"url_for('admin.{ep}'")
                    content = content.replace(f'url_for("{ep}"', f'url_for("admin.{ep}"')
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

if __name__ == '__main__':
    update_templates()
    print("Templates updated with blueprint prefixes.")
