import os

def fix_layouts():
    with open('templates/admin/dashboard.html', 'r', encoding='utf-8') as f:
        dash = f.read()
        
    # Extract the header and sidebar from dashboard
    start_main = dash.find('<!-- Main Content -->')
    if start_main == -1: return
    head_and_sidebar = dash[:start_main]

    files_to_fix = ['templates/admin/products.html', 'templates/admin/orders.html']
    
    for filename in files_to_fix:
        if not os.path.exists(filename): continue
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        main_start = content.find('<!-- Main Content -->')
        if main_start == -1:
            print(f"Could not find Main Content in {filename}")
            continue
            
        # The content after <!-- Main Content -->
        tail = content[main_start:]
        
        # In the head_and_sidebar, we need to fix the <title> and active class.
        # But for now, just injecting it is 90% better than the broken layout.
        # Let's fix the active class slightly if we want.
        new_head = head_and_sidebar.replace('class="side-link active"', 'class="side-link"')
        if 'products' in filename:
            new_head = new_head.replace('url_for(\'admin.admin_products\') }}" class="side-link"', 'url_for(\'admin.admin_products\') }}" class="side-link active"')
            new_head = new_head.replace('<title>Executive Analytics', '<title>Products')
        elif 'orders' in filename:
            new_head = new_head.replace('url_for(\'admin.admin_orders\') }}" class="side-link"', 'url_for(\'admin.admin_orders\') }}" class="side-link active"')
            new_head = new_head.replace('<title>Executive Analytics', '<title>Orders')
            
        # Write back
        # Note: the old templates had <div class="col-md-10 px-0"> directly wrapping the main content.
        # Our new sidebar uses <div class="admin-main">. Let's make sure the tail starts with <div class="admin-main">
        # Let's cleanly replace the <div class="col-md-10 px-0"> with <div class="admin-main">
        
        tail = tail.replace('<div class="col-md-10 px-0">', '<div class="admin-main">')
        tail = tail.replace('<div class="col-md-9 px-0">', '<div class="admin-main">') # Just in case
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_head + tail)
            
        print(f"Fixed layout for {filename}")

if __name__ == '__main__':
    fix_layouts()
