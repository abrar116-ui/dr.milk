import os

def fix_routes():
    user_endpoints = ['home', 'login', 'signup', 'logout', 'add_to_cart', 'remove_from_cart', 'checkout', 'view_cart', 'user_orders', 'profile']
    admin_endpoints = ['admin_login', 'admin_dashboard', 'admin_users', 'admin_user_profile', 'admin_products', 'admin_add_product', 'admin_delete_product', 'admin_orders', 'update_order_status', 'admin_delete_order', 'export_report', 'admin_quick_delivery']

    files_to_check = ['routes/user_routes.py', 'routes/admin_routes.py']

    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix user endpoints
        for ep in user_endpoints:
            content = content.replace(f"url_for('{ep}')", f"url_for('user.{ep}')")
            content = content.replace(f'url_for("{ep}")', f'url_for("user.{ep}")')

        # Fix admin endpoints
        for ep in admin_endpoints:
            content = content.replace(f"url_for('{ep}')", f"url_for('admin.{ep}')")
            content = content.replace(f'url_for("{ep}")', f'url_for("admin.{ep}")')

        # Also there's one more url_for which might have params.
        # Let's just do it broadly: url_for('ep'
        for ep in user_endpoints:
            content = content.replace(f"url_for('{ep}'", f"url_for('user.{ep}'")
            content = content.replace(f'url_for("{ep}"', f'url_for("user.{ep}"')
            
        for ep in admin_endpoints:
            # We already fixed 'admin.admin_login' in the decorator manually earlier, let's avoid double prefix 'admin.admin.admin_login'
            # To be safe, first revert double prefix if we accidentally create them
            content = content.replace(f"url_for('{ep}'", f"url_for('admin.{ep}'")
            content = content.replace(f'url_for("{ep}"', f'url_for("admin.{ep}"')
            
        content = content.replace("admin.admin.", "admin.")
        content = content.replace("user.user.", "user.")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == '__main__':
    fix_routes()
    print("Python routes fixed!")
