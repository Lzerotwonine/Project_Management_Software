from pymongo import MongoClient
from datetime import datetime
import random

def connect_to_mongodb():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['QuanLyDuAnPhanMem']
    collection = db['SanPham']
    return collection

# Danh sách các trạng thái
statuses = ["Đã giao", "Đang vận chuyển", "Đã xác nhận"]

# Kết nối đến cơ sở dữ liệu MongoDB
collection = connect_to_mongodb()

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
