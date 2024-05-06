from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import Flask, flash, jsonify, request
from flask import Flask, render_template, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import FileField, FloatField, HiddenField, IntegerField, SelectField, StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
import os
from wtforms import HiddenField
from flask_wtf.file import FileField, FileAllowed
from werkzeug.datastructures import MultiDict
from wtforms import ValidationError
from wtforms.validators import NumberRange
from bson import ObjectId
from flask import jsonify


app = Flask(__name__)

app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = 'static/images'


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def connect_to_mongodb(collection_name):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['QuanLyDuAnPhanMem']
    collection = db[collection_name]
    return collection

app.config['SECRET_KEY'] = 'your-secret-key'

@app.route('/', methods=['GET', 'POST'])
@app.route("/login", methods=['GET', 'POST'])
def login():
    return do_login()

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

def do_login():
    form = LoginForm()
    if form.validate_on_submit():
        account = connect_to_mongodb('TaiKhoan')
        user = account.find_one({"email": form.email.data})
        if user and check_password_hash(user["password"], form.password.data):
            # Lưu thông tin đăng nhập vào session
            session['logged_in'] = True
            session['username'] = user['username']  # Lưu username vào session
            return redirect(url_for('home'))
        
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    # Xóa thông tin đăng nhập khỏi session
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = {"username": form.username.data, "email": form.email.data, "password": hashed_password}
        account = connect_to_mongodb('TaiKhoan')
        account.insert_one(user)
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html', title='Home')


@app.route('/products', methods=['GET'])
def products():
    # Kết nối đến cơ sở dữ liệu MongoDB
    collection = connect_to_mongodb('SanPham')

    # Lấy danh sách sản phẩm từ cơ sở dữ liệu
    # Chỉ lấy các document có đầy đủ các trường cần thiết
    products = collection.find({
        "name": { "$exists": True },
        "description": { "$exists": True },
        "price": { "$exists": True },
        "quantity_in_stock": { "$exists": True },
        "image_path": { "$exists": True },
        "nha_phan_phoi": { "$exists": True }
    })

    # Hiển thị trang 'products.html' với danh sách sản phẩm
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        # Lấy thông tin sản phẩm từ form
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        quantity_in_stock = request.form.get('quantity_in_stock')
        nha_phan_phoi = request.form.get('nha_phan_phoi')
        if price < '0' or int(quantity_in_stock) < 0:
            return render_template('add_product.html')
        # Lưu hình ảnh đã tải lên
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            else:
                image_path = ''
        else:
            image_path = ''


        # Tạo một sản phẩm mới
        product = {
            "name": name,
            "description": description,
            "price": price,
            "quantity_in_stock": quantity_in_stock,
            "image_path": image_path,
            "nha_phan_phoi": nha_phan_phoi
        }

        # Thêm sản phẩm mới vào cơ sở dữ liệu
        collection = connect_to_mongodb('SanPham')
        collection.insert_one(product)

        # Hiển thị thông báo và chuyển hướng người dùng
        flash('Sản phẩm đã được thêm thành công!')
        return redirect(url_for('products'))

    # Hiển thị form thêm sản phẩm
    return render_template('add_product.html')

class EditProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])
    quantity_in_stock = IntegerField('Quantity in Stock', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(app.config['ALLOWED_EXTENSIONS'])])
    submit = SubmitField('Update Product')


@app.route('/edit_product/<id>', methods=['GET', 'POST'])
def edit_product(id):
    collection = connect_to_mongodb('SanPham')
    product = collection.find_one({"_id": ObjectId(id)})

    if request.method == 'POST':
        # Lấy thông tin sản phẩm từ form
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        quantity_in_stock = request.form.get('quantity_in_stock')

        # Kiểm tra giá và số lượng phải lớn hơn 0
        if float(price) <= 0 or int(quantity_in_stock) <= 0:
            flash('Giá và số lượng phải lớn hơn 0!')
            return render_template('edit_product.html', product=product)

        # Lưu hình ảnh đã tải lên
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            else:
                image_path = product["image_path"]
        else:
            image_path = product["image_path"]

        # Cập nhật sản phẩm
        product = {
            "name": name,
            "description": description,
            "price": price,
            "quantity_in_stock": quantity_in_stock,
            "image_path": image_path
        }

        # Cập nhật sản phẩm trong cơ sở dữ liệu
        collection.update_one({"_id": ObjectId(id)}, {"$set": product})

        # Hiển thị thông báo và chuyển hướng người dùng
        flash('Sản phẩm đã được cập nhật thành công!')
        return redirect(url_for('products'))

    # Hiển thị form chỉnh sửa sản phẩm
    return render_template('edit_product.html', product=product)





@app.route('/delete_product/<id>', methods=['GET', 'POST'])
def delete_product(id):
    collection = connect_to_mongodb('SanPham')
    product = collection.find_one({"_id": ObjectId(id)})

    if request.method == 'POST':
        collection.delete_one({"_id": ObjectId(id)})
        flash('Sản phẩm đã được xóa thành công!')
        last_query = session.get('last_query')
        last_sort_by = session.get('last_sort_by')
        last_order = session.get('last_order')
        if last_query:
            return redirect(url_for('search', query=last_query))
        elif last_sort_by and last_order:
            return redirect(url_for('sort', sort_by=last_sort_by, order=last_order))
        else:
            return redirect(url_for('products'))
    else:
        return render_template('delete_product.html', product=product)


def get_products():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['QuanLyDuAnPhanMem']
    collection = db['SanPham']
    products = collection.find()
    return [(product['_id'], product['name']) for product in products if 'name' in product]

def get_product_quantity(product_id):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['QuanLyDuAnPhanMem']
    collection = db['SanPham']
    product = collection.find_one({"_id": ObjectId(product_id)})
    return product['quantity_in_stock'] if product and 'quantity_in_stock' in product else 0

class OrderForm(FlaskForm):
    customer_name = StringField('Customer Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    phone_number = StringField('Số điện thoại', validators=[DataRequired()])
    product_name = SelectField('Tên sản phẩm', choices=[])
    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.product_name.choices = get_products()
    quantity = IntegerField('Số lượng', validators=[DataRequired(), NumberRange(min=1, max=None)])
    price = FloatField('Price', validators=[DataRequired()])
    submit = SubmitField('Place Order')

    def validate_quantity(self, field):
        max_quantity = int(get_product_quantity(self.product_name.data))  # Chuyển đổi max_quantity thành int
        if field.data > max_quantity:
            raise ValidationError(f'Số lượng tối đa bạn có thể đặt là {max_quantity}')
        elif field.data < 0:
            raise ValidationError('Số lượng không thể âm')




def connect_to_orders_db():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['QuanLyDuAnPhanMem']
    collection = db['DonHang']  # new collection for orders
    return collection

@app.route('/product_price', methods=['GET'])
def product_price():
    product_id = request.args.get('product_id')
    collection = connect_to_mongodb('SanPham')
    product = collection.find_one({"_id": ObjectId(product_id)})
    return jsonify(product['price'] if 'price' in product else 0)

def connect_to_sold_products_db():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['QuanLyDuAnPhanMem']
    collection = db['SanPhamDaBan']  # new collection for sold products
    return collection

@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    form = OrderForm()
    if form.validate_on_submit():
        print("Form data:", form.data)  # print form data for debugging
        product_collection = connect_to_mongodb('SanPham')
        product = product_collection.find_one({"_id": ObjectId(form.product_name.data)})
        order = {
            "customer_name": form.customer_name.data,
            "address": form.address.data,
            "phone_number": form.phone_number.data,
            "product_id": form.product_name.data,  # Lưu _id của sản phẩm
            "quantity": form.quantity.data,
            "price": int(form.quantity.data) * int(product['price'])  # Chuyển đổi quantity và price thành int và Cập nhật giá dựa trên số lượng đặt hàng
        }

        # Thêm đơn hàng mới vào cơ sở dữ liệu
        collection = connect_to_orders_db()  # this connects to the DonHang collection
        result = collection.insert_one(order)
        print("Insert result:", result)  # print insert result for debugging

        # Cập nhật số lượng sản phẩm trong kho
        product_collection = connect_to_mongodb('SanPham')
        product = product_collection.find_one({"_id": ObjectId(order['product_id'])})
        if product and 'quantity_in_stock' in product:
            new_quantity_in_stock = int(product['quantity_in_stock']) - order['quantity']
            product_collection.update_one({"_id": ObjectId(order['product_id'])}, {"$set": {"quantity_in_stock": new_quantity_in_stock}})

        # Thêm thông tin vào document SanPhamDaBan
        sold_product_collection = connect_to_sold_products_db()  # new collection for sold products
        sold_product = {
            "name": product['name'],  # tên sản phẩm
            "quantity_sold": order['quantity'],  # số lượng đã bán
            "price_sold": int(form.quantity.data) * int(product['price']),  # giá bán
            "image_path": product['image_path']  # đường dẫn hình ảnh
        }
        sold_product_collection.insert_one(sold_product)

        # Hiển thị thông báo và chuyển hướng người dùng
        flash('Đơn hàng đã được thêm thành công!')
        return redirect(url_for('orders'))

    print("Form errors:", form.errors)  # print form errors for debugging
    # Hiển thị form thêm đơn hàng
    return render_template('add_order.html', form=form)


@app.route('/orders', methods=['GET'])
def orders():
    order_collection = connect_to_orders_db()
    product_collection = connect_to_mongodb('SanPham')  # this connects to the product collection
    orders = list(order_collection.find())  # convert cursor to list
    for order in orders:
        product_id = order.get('product_id')
        if product_id:
            product = product_collection.find_one({"_id": ObjectId(product_id)})
            if product:
                order['product_name'] = product['name']  # add product name to the order
    return render_template('orders.html', orders=orders)



@app.route('/product_names', methods=['GET'])
def product_names():
    collection = connect_to_mongodb('SanPham')
    products = collection.find({}, {"_id": 0, "name": 1})  # chỉ lấy trường 'name'
    product_names = [product['name'] for product in products if 'name' in product]
    return jsonify(product_names)



def get_inventory_report():
    collection = connect_to_mongodb('SanPham')
    products = collection.find({}, {"_id": 0, "name": 1, "quantity_in_stock": 1})  # chỉ lấy trường 'name' và 'quantity_in_stock'
    return jsonify(list(products))

@app.route('/inventory_report', methods=['GET'])
def inventory_report():
    return get_inventory_report()




@app.route('/top_selling_products', methods=['GET'])
def top_selling_products():
    sold_product_collection = connect_to_sold_products_db()
    sold_products = sold_product_collection.aggregate([
        {"$group": {"_id": "$name", "total_quantity": {"$sum": "$quantity_sold"}}},
        {"$sort": {"total_quantity": -1}},
        {"$limit": 5}
    ])
    top_selling_products = list(sold_products)
    # Thêm thông tin hình ảnh vào danh sách sản phẩm bán chạy nhất
    for product in top_selling_products:
        sold_product = sold_product_collection.find_one({"name": product["_id"]})
        if sold_product and "image_path" in sold_product:
            product["image_path"] = sold_product["image_path"]
    return jsonify(top_selling_products)



@app.route('/inventory_summary', methods=['GET'])
def inventory_summary():
    collection = connect_to_mongodb('SanPham')
    products = collection.find({}, {"_id": 0, "name": 1, "quantity_in_stock": 1, "price": 1})  # chỉ lấy trường 'name', 'quantity_in_stock' và 'price'
    total_quantity = sum(int(product['quantity_in_stock']) for product in products if 'quantity_in_stock' in product)
    total_value = sum(int(product['price']) * int(product['quantity_in_stock']) for product in products if 'price' in product and 'quantity_in_stock' in product)
    return jsonify({"total_quantity": total_quantity, "total_value": total_value})



@app.route('/low_stock_products', methods=['GET'])
def low_stock_products():
    collection = connect_to_mongodb('SanPham')
    pipeline = [
        {"$match": {"quantity_in_stock": {"$lt": 30}}},
        {"$project": {"_id": 0, "name": 1, "image_path": 1, "quantity_in_stock": 1}},
        {"$sort": {"quantity_in_stock": 1}},
    ]
    low_stock_products = collection.aggregate(pipeline)
    return jsonify(list(low_stock_products))
    # Thêm thông tin hình ảnh vào danh sách sản phẩm sắp hết
    for product in low_stock_products:
        product_info = product_collection.find_one({"_id": product["_id"]})
        if product_info and "image_path" in product_info:
            product["image_path"] = product_info["image_path"]
    return jsonify(low_stock_products)



@app.route('/distributors', methods=['GET'])
def distributors():
    # Kết nối đến cơ sở dữ liệu MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['QuanLyDuAnPhanMem']
    collection = db['NhaPhanPhoi']

    # Lấy danh sách nhà phân phối từ cơ sở dữ liệu
    distributors = collection.find()

    # Hiển thị trang 'distributors.html' với danh sách nhà phân phối
    return render_template('distributors.html', distributors=distributors)

def connect_to_mongodbNhaPhanPhoi():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['QuanLyDuAnPhanMem']
    return db['NhaPhanPhoi']

@app.route('/add_distributor', methods=['GET', 'POST'])

def add_distributor():
    if request.method == 'POST':
        # Chia chuỗi nhập vào thành một danh sách các tên sản phẩm
        san_pham_phan_phoi = request.form.get('san_pham_phan_phoi').split('\n')
        # Loại bỏ các dòng trống
        san_pham_phan_phoi = [san_pham for san_pham in san_pham_phan_phoi if san_pham]
        # Chuyển đổi danh sách các tên sản phẩm thành danh sách các đối tượng sản phẩm
        san_pham_phan_phoi = [{"name": san_pham} for san_pham in san_pham_phan_phoi]

        distributor = {
            "ten_nha_phan_phoi": request.form.get('ten_nha_phan_phoi'),
            "dia_chi": request.form.get('dia_chi'),
            "so_dien_thoai": request.form.get('so_dien_thoai'),
            "san_pham_phan_phoi": san_pham_phan_phoi
        }
        collection = connect_to_mongodbNhaPhanPhoi()
        collection.insert_one(distributor)
        return redirect(url_for('distributors'))
    return render_template('add_distributor.html')

@app.route('/edit_distributor/<id>', methods=['GET', 'POST'])

def edit_distributor(id):
    collection = connect_to_mongodbNhaPhanPhoi()
    if request.method == 'POST':
        # Chia chuỗi nhập vào thành một danh sách các tên sản phẩm
        san_pham_phan_phoi = request.form.get('san_pham_phan_phoi').split('\n')
        # Loại bỏ các dòng trống
        san_pham_phan_phoi = [san_pham for san_pham in san_pham_phan_phoi if san_pham]
        # Chuyển đổi danh sách các tên sản phẩm thành danh sách các đối tượng sản phẩm
        san_pham_phan_phoi = [{"name": san_pham} for san_pham in san_pham_phan_phoi]

        distributor = {
            "ten_nha_phan_phoi": request.form.get('ten_nha_phan_phoi'),
            "dia_chi": request.form.get('dia_chi'),
            "so_dien_thoai": request.form.get('so_dien_thoai'),
            "san_pham_phan_phoi": san_pham_phan_phoi  # Cập nhật danh sách sản phẩm phân phối
        }
        collection.update_one({"_id": ObjectId(id)}, {"$set": distributor})
        return redirect(url_for('distributors'))
    distributor = collection.find_one({"_id": ObjectId(id)})

    # Chuyển đổi danh sách sản phẩm thành chuỗi
    san_pham_phan_phoi = '\n'.join([san_pham['name'] for san_pham in distributor['san_pham_phan_phoi']])
    distributor['san_pham_phan_phoi'] = san_pham_phan_phoi
    return render_template('edit_distributor.html', distributor=distributor)

@app.route('/delete_distributor/<id>', methods=['GET', 'POST'])

def delete_distributor(id):
    collection = connect_to_mongodbNhaPhanPhoi()
    if request.method == 'POST':
        collection.delete_one({"_id": ObjectId(id)})
        return redirect(url_for('distributors'))
    distributor = collection.find_one({"_id": ObjectId(id)})
    return render_template('delete_distributor.html', distributor=distributor)



@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    session['last_query'] = query  # Lưu trữ truy vấn
    collection = connect_to_mongodb('SanPham')
    products = collection.find({"$or": [{"name": {"$regex": query, "$options": 'i'}}, {"nha_phan_phoi": {"$regex": query, "$options": 'i'}}]})
    return render_template('products.html', products=products)

@app.route('/sort', methods=['GET'])
def sort():
    sort_by = request.args.get('sort_by')
    order = request.args.get('order')
    session['last_sort_by'] = sort_by  # Lưu trữ trường sắp xếp
    session['last_order'] = order  # Lưu trữ thứ tự sắp xếp
    collection = connect_to_mongodb('SanPham')
    if order == 'asc':
        products = collection.find().sort(sort_by, 1)
    else:
        products = collection.find().sort(sort_by, -1)
    return render_template('products.html', products=products)



if __name__ == '__main__':
    app.run(debug=True)
