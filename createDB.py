from pymongo import MongoClient
from datetime import datetime
import random

def connect_to_mongodb(collection_name):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['QuanLyDuAnPhanMem']
    collection = db[collection_name]
    return collection

# Danh sách các trạng thái
statuses = ["Đã giao", "Đang vận chuyển", "Đã xác nhận"]

# Khi bạn muốn kết nối đến collection 'TaiKhoan':
account = connect_to_mongodb('TaiKhoan')

# Khi bạn muốn kết nối đến collection 'SanPham':
collection = connect_to_mongodb('SanPham')

# Tạo và thêm 10 đơn hàng với trạng thái ngẫu nhiên
for i in range(10, 21):
    order = {
        "id": f"order{i}",
        "date": datetime.now(),
        "order_number": i,
        "customer_name": f"Khách hàng {i}",
        "status": random.choice(statuses)
    }
    collection.insert_one(order)
