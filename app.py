from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, SelectField, FloatField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from models.product import Category, Product, ProductType, ContactMessage, AdminUser
from functools import wraps
import datetime
import sqlite3
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'floofofhearts-secret-key'  # Change this in production
csrf = CSRFProtect(app)  # Initialize CSRF protection

# Initialize the database connection (if needed, you can create a function to get connections)
def init_db():
    conn = sqlite3.connect('instance/floorofhearts.db')
    conn.close()

# Create a contact form class
class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Length(max=20)])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=2, max=100)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=1000)])
    submit = SubmitField('Send Message')

# Login form class for admin users
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Product Form for admin
class ProductForm(FlaskForm):
    product_id = StringField('Product ID', validators=[DataRequired(), Length(min=2, max=20)])
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    product_type_id = SelectField('Product Type', coerce=int, validators=[Optional()])
    price = FloatField('Price', validators=[Optional()])
    image_url = StringField('Image URL', validators=[Optional(), Length(max=200)])
    specifications = TextAreaField('Specifications (JSON)', validators=[Optional()])
    features = TextAreaField('Features (JSON Array)', validators=[Optional()])
    
    def validate_specifications(self, field):
        if field.data.strip():
            try:
                json.loads(field.data)
            except json.JSONDecodeError:
                raise ValidationError('Invalid JSON format for specifications')
                
    def validate_features(self, field):
        if field.data.strip():
            try:
                features = json.loads(field.data)
                if not isinstance(features, list):
                    raise ValidationError('Features must be a JSON array')
            except json.JSONDecodeError:
                raise ValidationError('Invalid JSON format for features')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login to access this page', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor to add data to all templates
@app.context_processor
def inject_data():
    return {
        'current_year': datetime.datetime.now().year,
        'categories': Category.query_all(),
    }

# Admin filter for Jinja templates
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to <br>"""
    if not value:
        return ''
    return value.replace('\n', '<br>')

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# About Us route
@app.route('/about')
def about():
    return render_template('about.html')

# Contact route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # Connect to the database
        try:
            conn = sqlite3.connect('instance/floorofhearts.db')
            cursor = conn.cursor()
            
            # Create contacts table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Insert the form data into the database
            cursor.execute('''
            INSERT INTO contacts (name, email, phone, subject, message)
            VALUES (?, ?, ?, ?, ?)
            ''', (
            form.name.data,
            form.email.data,
            form.phone.data,
            form.subject.data,
            form.message.data
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            flash(f'Error saving your message: {str(e)}', 'danger')
            return redirect(url_for('contact'))
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html', form=form)

# Category page route (e.g., LVT, Carpets, etc.)
@app.route('/category/<string:category_name>')
def category(category_name):
    category = Category.filter_by(slug=category_name)
    if not category:
        return render_template('404.html'), 404
        
    product_types = ProductType.filter_by(category_id=category.id)
    
    # Filter by product type if specified in the query parameters
    type_filter = request.args.get('type')
    if type_filter:
        product_type_list = [pt for pt in product_types if pt.slug == type_filter]
        if product_type_list:
            product_type = product_type_list[0]
            products = Product.filter_by(category_id=category.id, product_type_id=product_type.id)
        else:
            products = Product.filter_by(category_id=category.id)
    else:
        products = Product.filter_by(category_id=category.id)
    
    return render_template(
        'category.html', 
        category=category, 
        product_types=product_types, 
        products=products,
        active_category=category_name
    )

# Product page route
@app.route('/product/<string:product_id>')
def product(product_id):
    products = Product.filter_by(product_id=product_id)
    if not products:
        return render_template('404.html'), 404
        
    product = products[0]
    # Find the category for active menu highlighting
    category = Category.get(product.category_id)
    active_category = category.slug if category else None
    
    return render_template('product.html', product=product, active_category=active_category)

# Search route
@app.route('/search')
def search():
    query = request.args.get('search', '')
    if not query:
        return render_template('search.html', query='', results=[])
    
    # Search for products by name, description, or product_id
    # Use SQLite LIKE for searching
    condition = f"name LIKE '%{query}%' OR description LIKE '%{query}%' OR product_id LIKE '%{query}%'"
    results = Product.filter(condition)
    
    return render_template('search.html', query=query, results=results)

# ADMIN ROUTES

# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # If user is already logged in, redirect to dashboard
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Verify credentials
        user = AdminUser.verify_password(username, password)
        
        if user:
            # Store user ID in session
            session['admin_id'] = user.id
            session['admin_username'] = user.username
            session['admin_name'] = user.name
            
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('admin/login.html', form=form)

# Admin logout route
@app.route('/admin/logout')
def admin_logout():
    # Clear session data
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    session.pop('admin_name', None)
    
    flash('You have been logged out', 'success')
    return redirect(url_for('admin_login'))

# Admin dashboard route
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Get statistics for dashboard
    product_count = len(Product.query_all())
    category_count = len(Category.query_all())
    product_type_count = len(ProductType.query_all())
    
    # Get recent messages
    recent_messages = ContactMessage.query_all()[:5]  # Get top 5 most recent messages
    message_count = len(recent_messages)
    
    return render_template(
        'admin/dashboard.html',
        product_count=product_count,
        category_count=category_count,
        product_type_count=product_type_count,
        message_count=message_count,
        recent_messages=recent_messages
    )

# Admin products list route
@app.route('/admin/products')
@login_required
def admin_products():
    products = Product.query_all()
    categories = Category.query_all()
    product_types = ProductType.query_all()
    
    return render_template(
        'admin/products.html',
        products=products,
        categories=categories,
        product_types=product_types
    )

# Admin add product route
@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    form = ProductForm()
    
    # Populate the category and product type dropdown lists
    categories = Category.query_all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    product_types = ProductType.query_all()
    form.product_type_id.choices = [(0, 'None')] + [(pt.id, pt.name) for pt in product_types]
    
    if form.validate_on_submit():
        # Create a new product
        new_product = Product(
            product_id=form.product_id.data,
            name=form.name.data,
            description=form.description.data,
            category_id=form.category_id.data,
            product_type_id=form.product_type_id.data if form.product_type_id.data > 0 else None,
            image_url=form.image_url.data,
            price=form.price.data,
            specifications=form.specifications.data,
            features=form.features.data
        )
        
        Product.save(new_product)
        flash('Product added successfully', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/product_form.html', form=form)

# Admin edit product route
@app.route('/admin/products/edit/<string:product_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    products = Product.filter_by(product_id=product_id)
    if not products:
        flash('Product not found', 'danger')
        return redirect(url_for('admin_products'))
        
    product = products[0]
    form = ProductForm(obj=product)
    
    # Populate the category and product type dropdown lists
    categories = Category.query_all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    product_types = ProductType.query_all()
    form.product_type_id.choices = [(0, 'None')] + [(pt.id, pt.name) for pt in product_types]
    
    if form.validate_on_submit():
        # Update the product
        product.name = form.name.data
        product.product_id = form.product_id.data
        product.description = form.description.data
        product.category_id = form.category_id.data
        product.product_type_id = form.product_type_id.data if form.product_type_id.data > 0 else None
        product.image_url = form.image_url.data
        product.price = form.price.data
        product.specifications = form.specifications.data
        product.features = form.features.data
        
        Product.save(product)
        flash('Product updated successfully', 'success')
        return redirect(url_for('admin_products'))
    
    # Pre-fill the form
    if product.specifications:
        form.specifications.data = json.dumps(product.get_specifications(), indent=2)
    if product.features:
        form.features.data = json.dumps(product.get_features(), indent=2)
    
    return render_template('admin/product_form.html', form=form, product=product)

# Admin delete product route
@app.route('/admin/products/delete/<string:product_id>', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    products = Product.filter_by(product_id=product_id)
    if not products:
        flash('Product not found', 'danger')
    else:
        Product.delete(product_id)
        flash('Product deleted successfully', 'success')
    
    return redirect(url_for('admin_products'))

# Admin categories list route
@app.route('/admin/categories')
@login_required
def admin_categories():
    categories = Category.query_all()
    return render_template('admin/categories.html', categories=categories)

# Admin add category route
@app.route('/admin/categories/add', methods=['POST'])
@login_required
def admin_add_category():
    # Get form data
    name = request.form.get('name')
    slug = request.form.get('slug')
    description = request.form.get('description')
    image_url = request.form.get('image_url')
    
    if not name or not slug:
        flash('Name and slug are required', 'danger')
        return redirect(url_for('admin_categories'))
    
    # Create a new category
    new_category = Category(
        name=name,
        slug=slug,
        description=description,
        image_url=image_url
    )
    
    Category.save(new_category)
    flash('Category added successfully', 'success')
    return redirect(url_for('admin_categories'))

# Admin edit category route
@app.route('/admin/categories/edit/<int:category_id>', methods=['POST'])
@login_required
def admin_edit_category(category_id):
    category = Category.get(category_id)
    if not category:
        flash('Category not found', 'danger')
        return redirect(url_for('admin_categories'))
    
    # Get form data
    name = request.form.get('name')
    slug = request.form.get('slug')
    description = request.form.get('description')
    image_url = request.form.get('image_url')
    
    if not name or not slug:
        flash('Name and slug are required', 'danger')
        return redirect(url_for('admin_categories'))
    
    # Update the category
    category.name = name
    category.slug = slug
    category.description = description
    category.image_url = image_url
    
    Category.save(category)
    flash('Category updated successfully', 'success')
    return redirect(url_for('admin_categories'))

# Admin delete category route
@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def admin_delete_category(category_id):
    category = Category.get(category_id)
    if not category:
        flash('Category not found', 'danger')
    else:
        # Check if category has products
        products = Product.filter_by(category_id=category_id)
        if products:
            flash(f'Cannot delete category: {len(products)} products are associated with it', 'danger')
        else:
            Category.delete(category_id)
            flash('Category deleted successfully', 'success')
    
    return redirect(url_for('admin_categories'))

# Admin product types list route
@app.route('/admin/product-types')
@login_required
def admin_product_types():
    product_types = ProductType.query_all()
    categories = Category.query_all()
    return render_template('admin/product_types.html', product_types=product_types, categories=categories)

# Admin add product type route
@app.route('/admin/product-types/add', methods=['POST'])
@login_required
def admin_add_product_type():
    # Get form data
    name = request.form.get('name')
    slug = request.form.get('slug')
    category_id = request.form.get('category_id')
    description = request.form.get('description')
    
    if not name or not slug or not category_id:
        flash('Name, slug, and category are required', 'danger')
        return redirect(url_for('admin_product_types'))
    
    # Create a new product type
    new_product_type = ProductType(
        name=name,
        slug=slug,
        category_id=int(category_id),
        description=description
    )
    
    ProductType.save(new_product_type)
    flash('Product type added successfully', 'success')
    return redirect(url_for('admin_product_types'))

# Admin edit product type route
@app.route('/admin/product-types/edit/<int:product_type_id>', methods=['POST'])
@login_required
def admin_edit_product_type(product_type_id):
    product_type = ProductType.get(product_type_id)
    if not product_type:
        flash('Product type not found', 'danger')
        return redirect(url_for('admin_product_types'))
    
    # Get form data
    name = request.form.get('name')
    slug = request.form.get('slug')
    category_id = request.form.get('category_id')
    description = request.form.get('description')
    
    if not name or not slug or not category_id:
        flash('Name, slug, and category are required', 'danger')
        return redirect(url_for('admin_product_types'))
    
    # Update the product type
    product_type.name = name
    product_type.slug = slug
    product_type.category_id = int(category_id)
    product_type.description = description
    
    ProductType.save(product_type)
    flash('Product type updated successfully', 'success')
    return redirect(url_for('admin_product_types'))

# Admin delete product type route
@app.route('/admin/product-types/delete/<int:product_type_id>', methods=['POST'])
@login_required
def admin_delete_product_type(product_type_id):
    product_type = ProductType.get(product_type_id)
    if not product_type:
        flash('Product type not found', 'danger')
    else:
        # Check if product type has products
        products = Product.filter_by(product_type_id=product_type_id)
        if products:
            # Update products to remove the product type (set to NULL)
            for product in products:
                product.product_type_id = None
                Product.save(product)
        
        ProductType.delete(product_type_id)
        flash('Product type deleted successfully', 'success')
    
    return redirect(url_for('admin_product_types'))

# Admin messages list route
@app.route('/admin/messages')
@login_required
def admin_messages():
    contact_messages = ContactMessage.query_all()
    return render_template('admin/messages.html', contact_messages=contact_messages)

# Admin view message route
@app.route('/admin/messages/view/<int:message_id>')
@login_required
def admin_view_message(message_id):
    message = ContactMessage.get(message_id)
    if not message:
        flash('Message not found', 'danger')
        return redirect(url_for('admin_messages'))
    
    return render_template('admin/view_message.html', message=message)

# Admin delete message route
@app.route('/admin/messages/delete/<int:message_id>', methods=['POST'])
@login_required
def admin_delete_message(message_id):
    message = ContactMessage.get(message_id)
    if not message:
        flash('Message not found', 'danger')
    else:
        ContactMessage.delete(message_id)
        flash('Message deleted successfully', 'success')
    
    return redirect(url_for('admin_messages'))

# API routes for admin functions
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query_all()
    return jsonify([product.to_dict() for product in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    # Add authentication here
    data = request.json
    
    new_product = Product(
        product_id=data['product_id'],
        name=data['name'],
        description=data['description'],
        category_id=data['category_id'],
        product_type_id=data.get('product_type_id'),
        image_url=data.get('image_url', ''),
        price=data.get('price'),
        specifications=data.get('specifications', '{}'),
        features=data.get('features', '[]')
    )
    
    Product.save(new_product)
    return jsonify(new_product.to_dict()), 201

@app.route('/api/products/<string:product_id>', methods=['PUT'])
def update_product(product_id):
    # Add authentication here
    products = Product.filter_by(product_id=product_id)
    if not products:
        return jsonify({"error": "Product not found"}), 404
        
    product = products[0]
    data = request.json
    
    for key, value in data.items():
        if hasattr(product, key):
            setattr(product, key, value)
    
    Product.save(product)
    return jsonify(product.to_dict())

@app.route('/api/products/<string:product_id>', methods=['DELETE'])
def delete_product(product_id):
    # Add authentication here
    products = Product.filter_by(product_id=product_id)
    if not products:
        return jsonify({"error": "Product not found"}), 404
        
    Product.delete(product_id)
    return '', 204

if __name__ == '__main__':
    init_db()  # Initialize the database connection
    app.run(debug=True)