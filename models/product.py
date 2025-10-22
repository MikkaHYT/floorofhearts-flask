import json
import sqlite3
import datetime
import hashlib

# Helper function to get database connection
def get_db_connection():
    conn = sqlite3.connect('instance/floorofhearts.db')
    conn.row_factory = sqlite3.Row
    return conn

# Admin User class for authentication
class AdminUser:
    def __init__(self, id=None, username=None, password_hash=None, name=None, email=None, is_active=True, created_at=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.name = name
        self.email = email
        self.is_active = is_active
        self.created_at = created_at
    
    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM admin_users WHERE username = ?', (username,)).fetchone()
        conn.close()
        return user and AdminUser(**dict(user))
    
    @staticmethod
    def verify_password(username, password):
        user = AdminUser.get_by_username(username)
        if not user:
            return None
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user.password_hash == password_hash and user.is_active:
            return user
        return None
    
    @staticmethod
    def create_admin(username, password, name, email):
        # Check if username already exists
        existing_user = AdminUser.get_by_username(username)
        if existing_user:
            return False, "Username already exists"
        
        # Create a new admin user
        conn = get_db_connection()
        now = datetime.datetime.now().isoformat()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn.execute('''
            INSERT INTO admin_users (username, password_hash, name, email, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, name, email, True, now))
        
        conn.commit()
        conn.close()
        return True, "Admin user created successfully"
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at
        }

class Category:
    def __init__(self, id=None, name=None, slug=None, description=None, image_url=None):
        self.id = id
        self.name = name
        self.slug = slug
        self.description = description
        self.image_url = image_url

    @staticmethod
    def query_all():
        conn = get_db_connection()
        categories = conn.execute('SELECT * FROM categories').fetchall()
        conn.close()
        return [Category(**dict(category)) for category in categories]

    @staticmethod
    def filter_by(slug=None):
        conn = get_db_connection()
        if slug:
            category = conn.execute(
                'SELECT * FROM categories WHERE slug = ?', (slug,)
            ).fetchone()
            conn.close()
            return category and Category(**dict(category))
        return None

    @staticmethod
    def get(id):
        if id is None:
            return None
        conn = get_db_connection()
        category = conn.execute(
            'SELECT * FROM categories WHERE id = ?', (id,)
        ).fetchone()
        conn.close()
        return category and Category(**dict(category))

    @staticmethod
    def save(category):
        conn = get_db_connection()
        
        if category.id:
            # Update existing category
            conn.execute('''
                UPDATE categories SET 
                name = ?, slug = ?, description = ?, image_url = ?
                WHERE id = ?
            ''', (
                category.name, category.slug, category.description, 
                category.image_url, category.id
            ))
        else:
            # Create new category
            cursor = conn.execute('''
                INSERT INTO categories (name, slug, description, image_url)
                VALUES (?, ?, ?, ?)
            ''', (
                category.name, category.slug, category.description, category.image_url
            ))
            category.id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        return category
        
    @staticmethod
    def delete(category_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'image_url': self.image_url
        }

class ProductType:
    def __init__(self, id=None, name=None, slug=None, description=None, category_id=None):
        self.id = id
        self.name = name
        self.slug = slug
        self.description = description
        self.category_id = category_id

    @staticmethod
    def query_all():
        conn = get_db_connection()
        types = conn.execute('SELECT * FROM product_types').fetchall()
        conn.close()
        return [ProductType(**dict(product_type)) for product_type in types]
        
    @staticmethod
    def filter_by(slug=None, category_id=None):
        conn = get_db_connection()
        query = 'SELECT * FROM product_types WHERE 1=1'
        params = []
        
        if slug:
            query += ' AND slug = ?'
            params.append(slug)
        
        if category_id:
            query += ' AND category_id = ?'
            params.append(category_id)
            
        product_types = conn.execute(query, params).fetchall()
        conn.close()
        
        return [ProductType(**dict(product_type)) for product_type in product_types]

    @staticmethod
    def get(id):
        if id is None:
            return None
        conn = get_db_connection()
        product_type = conn.execute(
            'SELECT * FROM product_types WHERE id = ?', (id,)
        ).fetchone()
        conn.close()
        return product_type and ProductType(**dict(product_type))
        
    @staticmethod
    def save(product_type):
        conn = get_db_connection()
        
        if product_type.id:
            # Update existing product type
            conn.execute('''
                UPDATE product_types SET 
                name = ?, slug = ?, description = ?, category_id = ?
                WHERE id = ?
            ''', (
                product_type.name, product_type.slug, product_type.description, 
                product_type.category_id, product_type.id
            ))
        else:
            # Create new product type
            cursor = conn.execute('''
                INSERT INTO product_types (name, slug, description, category_id)
                VALUES (?, ?, ?, ?)
            ''', (
                product_type.name, product_type.slug, product_type.description, product_type.category_id
            ))
            product_type.id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        return product_type
        
    @staticmethod
    def delete(product_type_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM product_types WHERE id = ?', (product_type_id,))
        conn.commit()
        conn.close()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'category_id': self.category_id
        }

class Product:
    def __init__(self, id=None, product_id=None, name=None, description=None, 
                 category_id=None, product_type_id=None, image_url=None, 
                 image_urls=None, price=None, specifications=None, features=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.product_id = product_id
        self.name = name
        self.description = description
        self.category_id = category_id
        self.product_type_id = product_type_id
        self.image_url = image_url
        self.image_urls = image_urls
        self.price = price
        self.specifications = specifications
        self.features = features
        self.created_at = created_at
        self.updated_at = updated_at
        
    @staticmethod
    def query_all():
        conn = get_db_connection()
        products = conn.execute('SELECT * FROM products').fetchall()
        conn.close()
        return [Product(**dict(product)) for product in products]
        
    @staticmethod
    def filter_by(product_id=None, category_id=None, product_type_id=None):
        conn = get_db_connection()
        query = 'SELECT * FROM products WHERE 1=1'
        params = []
        
        if product_id:
            query += ' AND product_id = ?'
            params.append(product_id)
        
        if category_id:
            query += ' AND category_id = ?'
            params.append(category_id)
            
        if product_type_id:
            query += ' AND product_type_id = ?'
            params.append(product_type_id)
            
        products = conn.execute(query, params).fetchall()
        conn.close()
        
        return [Product(**dict(product)) for product in products]
        
    @staticmethod
    def filter(condition):
        conn = get_db_connection()
        query = 'SELECT * FROM products WHERE ' + condition
        products = conn.execute(query).fetchall()
        conn.close()
        return [Product(**dict(product)) for product in products]
    
    @staticmethod
    def save(product):
        conn = get_db_connection()
        now = datetime.datetime.now().isoformat()
        
        if product.id:
            # Update existing product
            conn.execute('''
                UPDATE products SET 
                product_id = ?, name = ?, description = ?, category_id = ?,
                product_type_id = ?, image_url = ?, image_urls = ?, price = ?,
                specifications = ?, features = ?, updated_at = ?
                WHERE id = ?
            ''', (
                product.product_id, product.name, product.description, product.category_id,
                product.product_type_id, product.image_url, product.image_urls, product.price,
                product.specifications, product.features, now, product.id
            ))
        else:
            # Create new product
            cursor = conn.execute('''
                INSERT INTO products (
                    product_id, name, description, category_id, product_type_id,
                    image_url, image_urls, price, specifications, features,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product.product_id, product.name, product.description, product.category_id,
                product.product_type_id, product.image_url, product.image_urls, product.price,
                product.specifications, product.features, now, now
            ))
            product.id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        return product
        
    @staticmethod
    def delete(product_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
        conn.commit()
        conn.close()
        
    def get_specifications(self):
        if self.specifications:
            return json.loads(self.specifications)
        return {}
    
    def get_features(self):
        if self.features:
            return json.loads(self.features)
        return []
    
    def get_image_urls(self):
        if self.image_urls:
            return json.loads(self.image_urls)
        return []
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'product_type_id': self.product_type_id,
            'image_url': self.image_url,
            'image_urls': self.get_image_urls(),
            'price': self.price,
            'specifications': self.get_specifications(),
            'features': self.get_features(),
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class ContactMessage:
    def __init__(self, id=None, name=None, email=None, phone=None, subject=None, message=None, created_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.subject = subject
        self.message = message
        self.created_at = created_at
    
    @staticmethod
    def query_all():
        conn = get_db_connection()
        messages = conn.execute('SELECT * FROM contacts ORDER BY created_at DESC').fetchall()
        conn.close()
        return [ContactMessage(**dict(msg)) for msg in messages]
    
    @staticmethod
    def get(id):
        if id is None:
            return None
        conn = get_db_connection()
        message = conn.execute('SELECT * FROM contacts WHERE id = ?', (id,)).fetchone()
        conn.close()
        return message and ContactMessage(**dict(message))
    
    @staticmethod
    def delete(id):
        conn = get_db_connection()
        conn.execute('DELETE FROM contacts WHERE id = ?', (id,))
        conn.commit()
        conn.close()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'subject': self.subject,
            'message': self.message,
            'created_at': self.created_at
        }