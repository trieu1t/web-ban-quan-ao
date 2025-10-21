import pandas as pd
# plotting
import matplotlib.pyplot as plt
#cau1
path = r"d:\python\auto_without_header.csv"

cols = [
    "symboling","normalized-losses","make","fuel-type","aspiration","num-of-doors",
    "body-style","drive-wheels","engine-location","wheel-base","length","width","height",
    "curb-weight","engine-type","num-of-cylinders","engine-size","fuel-system","bore",
    "stroke","compression-ratio","horsepower","peak-rpm","city-mpg","highway-mpg","price"
]

# Read CSV without header, interpret '?' as NaN
df = pd.read_csv(path, header=None, names=cols, na_values=['?'])

# Print dtypes and head(5)
print("Data types:\n", df.dtypes)
print("\nHead(5):\n", df.head(5))

# Câu 10: In thông tin thống kê chung của df (mặc định describe cho các cột số)
print("\nCau 10 - Thong tin thong ke chung (numeric):\n")
print(df.describe())

# Câu 11: Thống kê chung của các cột có kiểu dữ liệu object
print("\nCau 11 - Thong tin thong ke cho cac cot dtype=object:\n")
print(df.describe(include=['object']))

# Câu 12: Số lượng của mỗi loại hệ thống dẫn động (drive-wheels)
print("\nCau 12 - So luong moi drive-wheels:\n")
print(df['drive-wheels'].value_counts(dropna=False))

# Câu 15: Tính giá (price) trung bình của mỗi loại hệ dẫn động (drive-wheels)
print("\nCâu 15: Gia trung binh theo drive-wheels:\n")
print(df.groupby('drive-wheels')['price'].mean())

# Câu 19: Vẽ histogram cho cột price
print("\nCâu 19: Vẽ histogram cho cột 'price' và lưu ảnh vào d:\\python\\price_hist.png")
price_series = df['price'].dropna().astype(float)
plt.figure(figsize=(8,5))
plt.hist(price_series, bins=30, color='skyblue', edgecolor='black')
plt.title('Distribution of Car Prices')
plt.xlabel('Price')
plt.ylabel('Frequency')
plt.grid(axis='y', alpha=0.75)
out_path = r"d:\\python\\price_hist.png"
plt.tight_layout()
plt.savefig(out_path)
print(f"Saved histogram to: {out_path}")


