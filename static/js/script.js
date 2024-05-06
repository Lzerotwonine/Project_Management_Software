
    // Sử dụng fetch API để lấy dữ liệu từ các endpoint API của bạn
    fetch('/inventory_report')
    .then(response => response.json())
    .then(data => {
    // Tạo biểu đồ tồn kho
    new Chart(document.getElementById('inventoryChart'), {
        type: 'bar',  // Biểu đồ hình tròn
        data: {
            labels: data.map(item => item.name),  // Tên sản phẩm
            datasets: [{
                data: data.map(item => item.quantity_in_stock),  // Số lượng tồn kho
                backgroundColor: ['#BDE2B9', '#7CC674', '#4CB140', '#38812F', '#23511E']  // Màu sắc cho các phần của biểu đồ
            }]
        },
        options: {
            legend: {
                display: true,  // Hiển thị danh sách tên
                position: 'right'  // Đặt danh sách tên ở bên phải
            }
        }
    });
    // Hiển thị tổng số sản phẩm và tổng số lượng sản phẩm trong kho
    document.getElementById('totalProducts').textContent = 'TỔNG SỐ SẢN PHẨM TRONG KHO: ' + data.length;
});


    fetch('/top_selling_products')
    .then(response => response.json())
    .then(products => {
    var productList = document.getElementById('productList');
    for (var product of products) {
    var productDiv = document.createElement('div');
    productDiv.className = 'product-card'; // Thêm lớp CSS vào thẻ div
    if (product.image_path) {  // Kiểm tra nếu image_path tồn tại
    productDiv.innerHTML += `<img src="${product.image_path}" alt="${product._id}">`;
}
    productDiv.innerHTML += `
                        <p><b>${product._id}</b><p>
                        <p>Đã bán: ${product.total_quantity}</p>
                    `;
    productList.appendChild(productDiv);
}
});



    fetch('/inventory_summary')
    .then(response => response.json())
    .then(data => {
    document.getElementById('totalQuantity').textContent = 'TỔNG SỐ LƯỢNG HÀNG TRONG KHO: ' + data.total_quantity;
    document.getElementById('totalValue').textContent = 'Giá trị tổng cộng của kho hàng: ' + data.total_value + ' VND';
});

    fetch('/low_stock_products')
    .then(response => response.json())
    .then(products => {
    var lowStockProductList = document.getElementById('lowStockProductList');
    for (var product of products) {
    var productDiv = document.createElement('div');
    productDiv.className = 'product-card'; // Thêm lớp CSS vào thẻ div
    if (product.image_path) {  // Kiểm tra nếu image_path tồn tại
    productDiv.innerHTML += `<img src="${product.image_path}" alt="${product._id}">`;
}
    productDiv.innerHTML += `
                        <p><b>${product.name}</b><p>
                        <p>Số lượng trong kho: ${product.quantity_in_stock}</p>
                    `;
    lowStockProductList.appendChild(productDiv);
}
});
