# 🏖️ Beach Accommodation Finder

Đồ án môn **Tư duy Tính toán** - Năm 2  
Ứng dụng tìm kiếm nơi ở gần bãi biển bằng AI và OpenStreetMap

## 🎯 Tổng quan

Hệ thống giúp người dùng tìm kiếm và xếp hạng các nơi ở (homestay, khách sạn, resort) gần bãi biển ở Việt Nam dựa trên:
- Tên bãi biển (được làm sạch bằng AI)
- Mức giá mong muốn
- Loại hình nơi ở
- Cảm giác/không gian mong muốn

## 🧠 4 Trụ cột Tư duy Tính toán

### 1. Problem Analysis
- **Input:** Thông tin tìm kiếm từ người dùng (text tự do)
- **Output:** Top 3-5 nơi ở đã xếp hạng
- **AI Integration:** Gemini API làm sạch input

### 2. Decomposition & Pattern Recognition
Hệ thống được chia thành 4 giai đoạn:
- **Giai đoạn 1:** Streamlit UI
- **Giai đoạn 2:** Conversation Control
- **Giai đoạn 3:** Input Processing (4 patterns)
- **Giai đoạn 4:** Backend Execution (4 patterns)

### 3. Abstraction
Đơn giản hóa "nơi ở" thành object với 6 thuộc tính chính:
- `name`: Tên
- `location`: Tọa độ GPS
- `type`: Loại hình
- `tags`: Danh sách tags
- `score`: Điểm xếp hạng
- `distance`: Khoảng cách

### 4. Algorithm Design
8 patterns chính:
1. AI Cleaning (Gemini)
2. Validation + Geocoding (OSM Nominatim)
3. Normalize Filters
4. Build Search Request
5. Searching (OSM Overpass)
6. Normalize Output
7. Filter Results
8. Ranking

## 🛠️ Công nghệ

- **Python 3.8+**
- **Streamlit** - Giao diện web
- **Google Gemini API** - AI làm sạch input
- **OpenStreetMap APIs:**
  - Nominatim - Geocoding
  - Overpass - POI search
- **Geopy** - Tính khoảng cách

## 📦 Cài đặt

### 1. Clone repository
```bash
git clone <repo-url>
cd beach-accommodation-finder
```

### 2. Tạo virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình API key
```bash
cp .env.example .env
# Sửa file .env, thêm GEMINI_API_KEY
```

Lấy Gemini API key tại: https://makersuite.google.com/app/apikey

## 🚀 Chạy ứng dụng

```bash
streamlit run app.py
```

Truy cập: http://localhost:8501

## 📖 Hướng dẫn sử dụng

1. Nhập tên bãi biển (vd: "vung tau", "nha trang")
2. Chọn mức giá (Rẻ/Trung bình/Cao)
3. Chọn loại hình (Homestay/Hotel/Resort...)
4. Nhập cảm giác mong muốn (không bắt buộc)
5. Click "Tìm kiếm"
6. Xem kết quả top 5 đã xếp hạng

## 📊 Luồng xử lý

```
Input → Gemini Cleaning → OSM Geocoding → Normalize Filters 
→ Build Request → OSM Search → Normalize Output → Filter → Ranking → Display
```

## 🎓 Điểm nổi bật

✅ **Tích hợp AI** - Gemini sửa lỗi chính tả tự động  
✅ **Dữ liệu thực** - OpenStreetMap miễn phí, cập nhật  
✅ **UI thân thiện** - Streamlit đơn giản, đẹp  
✅ **Xếp hạng thông minh** - Kết hợp khoảng cách + tags  
✅ **Không cần database** - Đơn giản cho đồ án  

## 👨‍💻 Tác giả

**Trananhkhoa2929**  
Đồ án Tư duy Tính toán - Năm 2  
Ngày: 11/11/2025

## 📝 License

Educational Project - For learning purposes only