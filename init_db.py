import os
import sys
import json
import sqlite3

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def get_db_connection():
    conn = sqlite3.connect('instance/floorofhearts.db')
    conn.row_factory = sqlite3.Row
    return conn

def seed_database():
    """Seed the database with initial data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if categories table exists, if not create it
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        description TEXT,
        image_url TEXT
    )
    ''')
    
    # Check if product_types table exists, if not create it
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT NOT NULL,
        description TEXT,
        category_id INTEGER,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')
    
    # Check if products table exists, if not create it
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        description TEXT,
        category_id INTEGER,
        product_type_id INTEGER,
        image_url TEXT,
        image_urls TEXT,
        price REAL,
        specifications TEXT,
        features TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY (category_id) REFERENCES categories (id),
        FOREIGN KEY (product_type_id) REFERENCES product_types (id)
    )
    ''')

    # Check if admin_users table exists, if not create it
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TEXT
    )
    ''')
    
    # Check if we already have data
    cursor.execute('SELECT COUNT(*) FROM categories')
    if cursor.fetchone()[0] > 0:
        print("Database already seeded. Skipping.")
        conn.close()
        return
    
    # Create categories
    categories = [
        {
            'name': 'LVT',
            'slug': 'lvt',
            'description': 'Luxury Vinyl Tiles - durable and stylish flooring options',
            'image_url': '/static/images/categories/lvt.jpg'
        },
        {
            'name': 'Engineered Wood',
            'slug': 'engineered',
            'description': 'Engineered wood flooring combines the beauty of real wood with enhanced stability',
            'image_url': '/static/images/categories/engineered.jpg'
        },
        {
            'name': 'Carpets',
            'slug': 'carpets',
            'description': 'Soft, comfortable carpets for a cozy feel in your home',
            'image_url': '/static/images/categories/carpets.jpg'
        },
        {
            'name': 'Laminates',
            'slug': 'laminates',
            'description': 'Affordable and durable laminate flooring options',
            'image_url': '/static/images/categories/laminates.jpg'
        },
        {
            'name': 'Sisal',
            'slug': 'sisal',
            'description': 'Natural sisal flooring for an eco-friendly option',
            'image_url': '/static/images/categories/sisal.jpg'
        },
        {
            'name': 'Flatweaves',
            'slug': 'flatweaves',
            'description': 'Stylish flatweave carpets for a contemporary look',
            'image_url': '/static/images/categories/flatweaves.jpg'
        },
        {
            'name': 'Stair Runners',
            'slug': 'runners',
            'description': 'Beautiful stair runners to enhance your staircase',
            'image_url': '/static/images/categories/runners.jpg'
        },
        {
            'name': 'Taping',
            'slug': 'taping',
            'description': 'Professional carpet taping services',
            'image_url': '/static/images/categories/taping.jpg'
        }
    ]
    
    category_objects = {}
    for category_data in categories:
        cursor.execute('''
        INSERT INTO categories (name, slug, description, image_url)
        VALUES (?, ?, ?, ?)
        ''', (
            category_data['name'], 
            category_data['slug'], 
            category_data['description'], 
            category_data['image_url']
        ))
        category_id = cursor.lastrowid
        # Save the reference for later use
        category_objects[category_data['slug']] = {'id': category_id}
    
    conn.commit()
    
    # Create product types for LVT
    lvt_product_types = [
        {
            'name': 'Herringbone',
            'slug': 'herringbone',
            'description': 'Classic and timeless, herringbone LVT is perfect for any room',
            'category_id': category_objects['lvt']['id']
        },
        {
            'name': 'Chevron',
            'slug': 'chevron',
            'description': 'Make a statement with chevron LVT flooring',
            'category_id': category_objects['lvt']['id']
        },
        {
            'name': 'Plank',
            'slug': 'plank',
            'description': 'Get the look of real wood with plank LVT flooring',
            'category_id': category_objects['lvt']['id']
        },
        {
            'name': 'Click',
            'slug': 'click',
            'description': 'Easy to install with a click-lock system',
            'category_id': category_objects['lvt']['id']
        },
        {
            'name': 'Glue Down',
            'slug': 'glue-down',
            'description': 'Durable and secure with adhesive application',
            'category_id': category_objects['lvt']['id']
        }
    ]
    
    product_type_objects = {}
    for type_data in lvt_product_types:
        cursor.execute('''
        INSERT INTO product_types (name, slug, description, category_id)
        VALUES (?, ?, ?, ?)
        ''', (
            type_data['name'], 
            type_data['slug'], 
            type_data['description'], 
            type_data['category_id']
        ))
        product_type_id = cursor.lastrowid
        # Save the reference for later use
        product_type_objects[type_data['slug']] = {'id': product_type_id}
    
    conn.commit()
    
    # Create products
    products = [
        {
            'product_id': 'RT01',
            'name': 'J2 - Rustic Oak',
            'description': 'Rustic Oak is a timeless plank design that brings warmth and elegance to any room. Its durable click-lock system ensures easy installation and long-lasting performance.',
            'category_id': category_objects['lvt']['id'],
            'product_type_id': product_type_objects['plank']['id'],
            'image_url': '/static/images/RT01.jpg',
            'image_urls': json.dumps(['/static/images/RT01-2.jpg', '/static/images/RT01-3.jpg']),
            'price': None,  # Price on request
            'specifications': json.dumps({
                'Dimensions': '1200mm x 180mm',
                'Thickness': '5mm',
                'Wear Layer': '0.5mm',
                'Installation': 'Click-Lock System',
                'Waterproof': 'Yes'
            }),
            'features': json.dumps([
                'Easy-to-install click-lock system',
                'Scratch-resistant and waterproof surface',
                'Realistic wood grain texture',
                'Perfect for both residential and commercial spaces'
            ])
        },
        {
            'product_id': 'NT45',
            'name': 'J2 - Taupe Brushed Oak',
            'description': 'Taupe Brushed Oak offers a sophisticated, contemporary look with its brushed texture and warm taupe tones. Ideal for modern interiors seeking a touch of elegance.',
            'category_id': category_objects['lvt']['id'],
            'product_type_id': product_type_objects['plank']['id'],
            'image_url': '/static/images/NT45.jpg',
            'image_urls': json.dumps(['/static/images/NT45-2.jpg']),
            'price': None,  # Price on request
            'specifications': json.dumps({
                'Dimensions': '1220mm x 180mm',
                'Thickness': '6mm',
                'Wear Layer': '0.55mm',
                'Installation': 'Click-Lock System',
                'Waterproof': 'Yes'
            }),
            'features': json.dumps([
                'Premium 0.55mm wear layer for high durability',
                'Realistic brushed oak texture',
                'Click-lock installation system',
                'Waterproof construction suitable for all rooms'
            ])
        },
        {
            'product_id': 'NTP43',
            'name': 'J2 - Carpenters Oak',
            'description': 'Carpenters Oak is a premium flooring option that combines natural beauty with exceptional durability. Its authentic wood grain texture and waterproof design make it ideal for any space.',
            'category_id': category_objects['lvt']['id'],
            'product_type_id': product_type_objects['plank']['id'],
            'image_url': '/static/images/NTP43.jpg',
            'image_urls': json.dumps(['/static/images/NTP43-2.jpg']),
            'price': None,  # Price on request
            'specifications': json.dumps({
                'Dimensions': '1220mm x 180mm',
                'Thickness': '6mm',
                'Wear Layer': '0.55mm',
                'Installation': 'Click-Lock System',
                'Waterproof': 'Yes'
            }),
            'features': json.dumps([
                'Easy-to-install click-lock system',
                'Scratch-resistant and waterproof surface',
                'Realistic wood grain texture',
                'Perfect for both residential and commercial spaces'
            ])
        },
        {
            'product_id': 'RTP02',
            'name': 'J2 - Golden Oak',
            'description': 'Golden Oak features a warm, rich finish that brightens any room. The perfect blend of traditional style with modern performance.',
            'category_id': category_objects['lvt']['id'],
            'product_type_id': product_type_objects['plank']['id'],
            'image_url': '/static/images/RTP02.jpg',
            'image_urls': json.dumps([]),
            'price': None,  # Price on request
            'specifications': json.dumps({
                'Dimensions': '1200mm x 180mm',
                'Thickness': '5mm',
                'Wear Layer': '0.5mm',
                'Installation': 'Click-Lock System',
                'Waterproof': 'Yes'
            }),
            'features': json.dumps([
                'Golden oak finish brings warmth to any space',
                'Durable wear layer for high-traffic areas',
                'Easy click-lock installation',
                'Waterproof and pet-friendly'
            ])
        }
    ]
    
    import datetime
    now = datetime.datetime.now().isoformat()
    
    for product_data in products:
        cursor.execute('''
        INSERT INTO products (
            product_id, name, description, category_id, product_type_id,
            image_url, image_urls, price, specifications, features,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_data['product_id'],
            product_data['name'],
            product_data['description'],
            product_data['category_id'],
            product_data['product_type_id'],
            product_data['image_url'],
            product_data['image_urls'],
            product_data['price'],
            product_data['specifications'],
            product_data['features'],
            now,
            now
        ))
    
    conn.commit()
    conn.close()
    print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()