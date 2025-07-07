import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Tạo dữ liệu nhân viên
np.random.seed(42)
employees = {
    "ID": range(1, 21),
    "Họ tên": [
        "Nguyễn Văn An",
        "Trần Thị Bình",
        "Lê Văn Cường",
        "Phạm Thị Dung",
        "Hoàng Văn Em",
        "Vũ Thị Phương",
        "Đặng Văn Giang",
        "Bùi Thị Hạnh",
        "Ngô Văn Inh",
        "Đinh Thị Kiều",
        "Dương Văn Long",
        "Mai Thị Minh",
        "Phan Văn Nam",
        "Tôn Thị Oanh",
        "Võ Văn Phúc",
        "Lý Thị Quỳnh",
        "Trương Văn Sơn",
        "Huỳnh Thị Tâm",
        "Đỗ Văn Uy",
        "Lưu Thị Vân",
    ],
    "Phòng ban": np.random.choice(["IT", "Kế toán", "Nhân sự", "Marketing", "Bán hàng"], 20),
    "Lương cơ bản": np.random.randint(8000000, 25000000, 20),
    "Ngày vào làm": pd.date_range(start="2020-01-01", end="2023-12-31", periods=20),
    "Tuổi": np.random.randint(22, 55, 20),
}

employees_df = pd.DataFrame(employees)
employees_df.to_excel("employees.xlsx", index=False)
print("✅ Đã tạo file employees.xlsx")

# Tạo dữ liệu bán hàng
start_date = datetime(2024, 1, 1)
sales_data = []

for i in range(50):
    date = start_date + timedelta(days=np.random.randint(0, 365))
    sales_data.append(
        {
            "Ngày bán": date,
            "Mã sản phẩm": f"SP{np.random.randint(1000, 9999)}",
            "Tên sản phẩm": np.random.choice(
                [
                    "Laptop Dell XPS",
                    "iPhone 15",
                    "Samsung Galaxy S24",
                    "MacBook Pro",
                    "iPad Air",
                    "AirPods Pro",
                    "Sony WH-1000XM5",
                    "Surface Pro",
                    "Gaming Mouse",
                    "Mechanical Keyboard",
                ]
            ),
            "Số lượng": np.random.randint(1, 20),
            "Đơn giá": np.random.randint(500000, 50000000),
            "Nhân viên bán": np.random.choice(employees_df["Họ tên"].tolist()),
            "Khách hàng": f"KH{np.random.randint(100, 999)}",
            "Ghi chú": np.random.choice(["Bán lẻ", "Bán buôn", "Khuyến mãi", "Đặt hàng online", ""]),
        }
    )

sales_df = pd.DataFrame(sales_data)
sales_df["Thành tiền"] = sales_df["Số lượng"] * sales_df["Đơn giá"]
sales_df = sales_df.sort_values("Ngày bán")
sales_df.to_excel("sales.xlsx", index=False)
print("✅ Đã tạo file sales.xlsx")
