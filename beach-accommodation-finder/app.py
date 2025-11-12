"""
Beach Accommodation Finder - Streamlit App
Đồ án Tư duy Tính toán - Năm 2

Author: Trananhkhoa2929
Date: 2025-11-11
"""

import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd

# Import các modules
from src.input_processing import (
    clean_location_input,
    validate_and_geocode,
    normalize_filters,
    build_search_request
)
from src.backend_execution import (
    search_accommodations,
    normalize_osm_data,
    filter_results,
    rank_results
)
from src.utils import format_distance

# Load environment variables
load_dotenv()

# ============================================================================
# STREAMLIT PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Beach Accommodation Finder",
    page_icon="🏖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SIDEBAR - THÔNG TIN DỰ ÁN
# ============================================================================

with st.sidebar:
    st.title("ℹ️ Thông tin Dự án")
    st.markdown("""
    **Đồ án:** Tư duy Tính toán  
    **Năm:** 2  
    **Sinh viên:** Trananhkhoa2929  
    **Ngày:** 11/11/2025
    
    ---
    
    ### 🎯 4 Trụ cột Tư duy Tính toán:
    1. ✅ **Problem Analysis**
    2. ✅ **Decomposition & Pattern Recognition**
    3. ✅ **Abstraction**
    4. ✅ **Algorithm Design**
    
    ---
    
    ### 🛠️ Công nghệ sử dụng:
    - 🤖 **Gemini API** (AI cleaning)
    - 🗺️ **OpenStreetMap** (Geocoding & Search)
    - 🎨 **Streamlit** (UI)
    """)

# ============================================================================
# MAIN APP
# ============================================================================

st.title("🏖️ Beach Accommodation Finder")
st.markdown("*Tìm kiếm nơi ở gần bãi biển bằng AI và OpenStreetMap*")

st.divider()

# ============================================================================
# KIỂM TRA API KEY
# ============================================================================

gemini_api_key = os.getenv('GEMINI_API_KEY')

if not gemini_api_key:
    st.error("⚠️ Chưa cấu hình GEMINI_API_KEY!")
    st.info("""
    **Hướng dẫn:**
    1. Tạo file `.env` trong thư mục gốc
    2. Thêm dòng: `GEMINI_API_KEY=your_api_key_here`
    3. Lấy API key tại: https://makersuite.google.com/app/apikey
    """)
    st.stop()

# ============================================================================
# FORM NHẬP LIỆU
# ============================================================================

st.subheader("📝 Nhập thông tin tìm kiếm")

with st.form("search_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        location_input = st.text_input(
            "🌊 Tên bãi biển *",
            placeholder="vd: Vũng Tàu, Nha Trang, Đà Nẵng...",
            help="Nhập tên bãi biển hoặc thành phố ven biển"
        )
        
        budget_input = st.selectbox(
            "💰 Mức giá *",
            options=["Rẻ", "Trung bình", "Cao"],
            help="Chọn mức giá phù hợp với ngân sách"
        )
    
    with col2:
        type_input = st.selectbox(
            "🏠 Loại hình nơi ở *",
            options=["Homestay", "Khách sạn", "Resort", "Villa", "Hostel"],
            help="Chọn loại hình nơi ở bạn muốn"
        )
        
        ambiance_input = st.text_input(
            "✨ Cảm giác mong muốn (không bắt buộc)",
            placeholder="vd: yên tĩnh, gần biển, lãng mạn...",
            help="Mô tả cảm giác bạn muốn (có thể để trống)"
        )
    
    submitted = st.form_submit_button("🔍 Tìm kiếm", use_container_width=True, type="primary")

# ============================================================================
# XỬ LÝ KHI SUBMIT FORM
# ============================================================================

if submitted:
    # Validate input
    if not location_input or location_input.strip() == "":
        st.error("❌ Vui lòng nhập tên bãi biển!")
        st.stop()
    
    # Hiển thị progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # ====================================================================
        # BƯỚC 1: AI CLEANING (Giai đoạn 3 - Pattern 1)
        # ====================================================================
        status_text.text("🤖 Đang làm sạch input bằng Gemini AI...")
        progress_bar.progress(10)
        
        cleaned_location, error = clean_location_input(location_input, gemini_api_key)
        
        if error:
            st.error(f"❌ Lỗi AI Cleaning: {error}")
            st.stop()
        
        st.success(f"✅ Đã làm sạch: **{location_input}** → **{cleaned_location}**")
        
        # ====================================================================
        # BƯỚC 2: GEOCODING + VALIDATION (Giai đoạn 3 - Pattern 2)
        # ====================================================================
        status_text.text("🗺️ Đang xác thực địa điểm và lấy tọa độ...")
        progress_bar.progress(30)
        
        geo_data, error = validate_and_geocode(cleaned_location)
        
        if error:
            st.error(f"❌ Lỗi Geocoding: {error}")
            st.stop()
        
        st.success(f"✅ Tìm thấy: **{geo_data['name']}** (Lat: {geo_data['lat']:.4f}, Lon: {geo_data['lon']:.4f})")
        
        # ====================================================================
        # BƯỚC 3: NORMALIZE FILTERS (Giai đoạn 3 - Pattern 3)
        # ====================================================================
        status_text.text("🔄 Đang chuẩn hóa filters...")
        progress_bar.progress(40)
        
        filters = normalize_filters(budget_input, type_input, ambiance_input)
        
        with st.expander("🔍 Xem filters đã chuẩn hóa"):
            st.json(filters)
        
        # ====================================================================
        # BƯỚC 4: BUILD SEARCH REQUEST (Giai đoạn 3 - Pattern 4)
        # ====================================================================
        status_text.text("📦 Đang xây dựng search request...")
        progress_bar.progress(50)
        
        search_request = build_search_request(geo_data, filters)
        
        # ====================================================================
        # BƯỚC 5: SEARCHING (Giai đoạn 4 - Pattern 5)
        # ====================================================================
        status_text.text("🔍 Đang tìm kiếm trên OpenStreetMap...")
        progress_bar.progress(60)
        
        osm_elements, error = search_accommodations(search_request)
        
        if error:
            st.warning(f"⚠️ {error}")
            st.info("💡 Thử tìm kiếm với loại hình khác hoặc địa điểm khác")
            st.stop()
        
        st.info(f"📊 Tìm thấy {len(osm_elements)} kết quả thô từ OSM")
        
        # ====================================================================
        # BƯỚC 6: NORMALIZE OUTPUT (Giai đoạn 4 - Pattern 6)
        # ====================================================================
        status_text.text("🔄 Đang chuẩn hóa dữ liệu...")
        progress_bar.progress(70)
        
        normalized = normalize_osm_data(osm_elements)
        
        st.info(f"✅ Đã chuẩn hóa {len(normalized)} nơi ở")
        
        # ====================================================================
        # BƯỚC 7: FILTER (Giai đoạn 4 - Pattern 7)
        # ====================================================================
        status_text.text("🔎 Đang lọc kết quả...")
        progress_bar.progress(80)
        
        filtered = filter_results(normalized, search_request)
        
        if not filtered or len(filtered) == 0:
            st.warning("⚠️ Không tìm thấy nơi ở phù hợp với yêu cầu")
            st.info("💡 Thử giảm yêu cầu về tags hoặc mở rộng bán kính tìm kiếm")
            st.stop()
        
        st.info(f"✅ Còn lại {len(filtered)} nơi ở sau khi lọc")
        
        # ====================================================================
        # BƯỚC 8: RANKING (Giai đoạn 4 - Pattern 8)
        # ====================================================================
        status_text.text("⭐ Đang xếp hạng kết quả...")
        progress_bar.progress(90)
        
        ranked = rank_results(filtered, search_request)
        
        # ====================================================================
        # HOÀN THÀNH
        # ====================================================================
        progress_bar.progress(100)
        status_text.text("✅ Hoàn thành!")
        
        st.balloons()
        
        # ====================================================================
        # HIỂN THỊ KẾT QUẢ
        # ====================================================================
        st.divider()
        st.subheader(f"🎯 Top {len(ranked)} nơi ở được đề xuất")
        
        # Tạo DataFrame để hiển thị
        df_data = []
        for acc in ranked:
            df_data.append({
                'Hạng': f"#{acc['rank']}",
                'Tên': acc['name'],
                'Loại': acc['type'],
                'Khoảng cách': format_distance(acc['distance']),
                'Điểm': f"{acc['score']:.1f}",
                'Tags': ', '.join(acc['tags'][:3])  # Hiển thị 3 tags đầu
            })
        
        df = pd.DataFrame(df_data)
        
        # Hiển thị bảng với styling
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Hiển thị chi tiết từng kết quả
        st.divider()
        st.subheader("📋 Chi tiết từng nơi ở")
        
        for acc in ranked:
            with st.expander(f"#{acc['rank']} - {acc['name']} ⭐ {acc['score']:.1f}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Khoảng cách", format_distance(acc['distance']))
                
                with col2:
                    st.metric("Loại hình", acc['type'])
                
                with col3:
                    st.metric("Điểm số", f"{acc['score']:.1f}")
                
                st.markdown("**Tags:**")
                st.write(", ".join(acc['tags']))
                
                st.markdown("**Tọa độ:**")
                st.code(f"Lat: {acc['location'][0]:.6f}, Lon: {acc['location'][1]:.6f}")
                
                # Link Google Maps
                gmaps_url = f"https://www.google.com/maps/search/?api=1&query={acc['location'][0]},{acc['location'][1]}"
                st.markdown(f"[📍 Xem trên Google Maps]({gmaps_url})")
        
    except Exception as e:
        st.error(f"❌ Lỗi không xác định: {str(e)}")
        st.exception(e)
    
    finally:
        progress_bar.empty()
        status_text.empty()

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Đồ án Tư duy Tính toán - Năm 2 | Trananhkhoa2929 | 2025</p>
    <p>Powered by 🤖 Gemini AI + 🗺️ OpenStreetMap + 🎨 Streamlit</p>
</div>
""", unsafe_allow_html=True)