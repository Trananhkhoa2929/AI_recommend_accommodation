"""
GIAI ĐOẠN 3: Input Processing & Enrichment
Bao gồm: AI Cleaning, Validation, Normalize, Intake Information
"""

import os
import requests
import time
from typing import Tuple, Dict, List, Optional
import google.generativeai as genai


# ============================================================================
# PATTERN 1: AI INPUT CLEANING (Gemini API)
# ============================================================================

def clean_location_input(raw_text: str, api_key: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Sử dụng Gemini API để làm sạch và sửa lỗi tên địa điểm
    
    Args:
        raw_text: Văn bản thô người dùng nhập
        api_key: Gemini API key
    
    Returns:
        Tuple (cleaned_text, error_message)
        - Nếu thành công: (cleaned_text, None)
        - Nếu lỗi: (None, error_message)
    """
    # Kiểm tra input rỗng
    if not raw_text or raw_text.strip() == "":
        return None, "Input không được để trống"
    
    try:
        # Cấu hình Gemini
        genai.configure(api_key=api_key)
        
        # ⚠️ THAY ĐỔI MODEL NAME - Dùng gemini-1.5-flash thay vì gemini-pro
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Xây dựng prompt
        prompt = f"""Bạn là trợ lý sửa lỗi địa danh Việt Nam.

User nhập: "{raw_text}"

Nhiệm vụ:
1. Sửa lỗi chính tả nếu có
2. Chuẩn hóa tên địa điểm (viết hoa đúng)
3. Nếu là tên bãi biển nổi tiếng ở Việt Nam, trả về tên đầy đủ

Chỉ trả về TÊN ĐỊA ĐIỂM đã sửa, không giải thích gì thêm.

Ví dụ:
- "vung tau" → "Vũng Tàu"
- "nha trang" → "Nha Trang"
- "da nang" → "Đà Nẵng"

Trả về:"""

        # Gọi API
        response = model.generate_content(prompt)
        
        # Kiểm tra response
        if not response or not response.text:
            return None, "Gemini API không trả về kết quả"
        
        cleaned = response.text.strip()
        
        # Validate cleaned text
        if len(cleaned) < 2 or len(cleaned) > 100:
            return None, "Tên địa điểm không hợp lệ"
        
        return cleaned, None
        
    except Exception as e:
        return None, f"Lỗi khi gọi Gemini API: {str(e)}"


# ============================================================================
# PATTERN 2: VALIDATION + GEOCODING (OpenStreetMap Nominatim)
# ============================================================================

def validate_and_geocode(location_name: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Xác thực địa điểm và lấy tọa độ GPS từ OpenStreetMap
    
    Args:
        location_name: Tên địa điểm đã được làm sạch
    
    Returns:
        Tuple (geo_data, error_message)
        - Nếu thành công: (geo_data_dict, None)
        - Nếu lỗi: (None, error_message)
    """
    try:
        # URL của Nominatim API
        url = "https://nominatim.openstreetmap.org/search"
        
        # Parameters
        params = {
            'q': f"{location_name}, Vietnam",
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        # Headers (bắt buộc phải có User-Agent)
        headers = {
            'User-Agent': 'BeachAccommodationFinder/1.0 (Educational Project)'
        }
        
        # Gọi API với delay để tránh rate limit
        time.sleep(1)
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Kiểm tra status code
        if response.status_code != 200:
            return None, f"Nominatim API trả về lỗi: {response.status_code}"
        
        # Parse JSON
        data = response.json()
        
        # Kiểm tra có kết quả không
        if not data or len(data) == 0:
            return None, f"Không tìm thấy địa điểm '{location_name}' ở Việt Nam"
        
        # Lấy kết quả đầu tiên
        result = data[0]
        
        # Extract thông tin
        geo_data = {
            'name': result.get('display_name', location_name),
            'lat': float(result['lat']),
            'lon': float(result['lon']),
            'type': result.get('type', 'unknown'),
            'importance': result.get('importance', 0)
        }
        
        return geo_data, None
        
    except requests.exceptions.Timeout:
        return None, "Timeout khi gọi Nominatim API (quá 10s)"
    except requests.exceptions.RequestException as e:
        return None, f"Lỗi kết nối Nominatim API: {str(e)}"
    except Exception as e:
        return None, f"Lỗi không xác định: {str(e)}"


# ============================================================================
# PATTERN 3: NORMALIZE INPUT FILTERS
# ============================================================================

def normalize_filters(budget_text: str, type_text: str, ambiance_text: str) -> Dict:
    """
    Chuẩn hóa các filter từ text sang giá trị chuẩn
    
    Args:
        budget_text: Mức giá (text tự do)
        type_text: Loại hình (text tự do)
        ambiance_text: Cảm giác mong muốn (text tự do)
    
    Returns:
        Dict chứa các giá trị đã chuẩn hóa
    """
    # Từ điển map budget
    budget_map = {
        'rẻ': 'low',
        'giá rẻ': 'low',
        'cheap': 'low',
        'bình thường': 'medium',
        'trung bình': 'medium',
        'normal': 'medium',
        'cao': 'high',
        'đắt': 'high',
        'sang trọng': 'high',
        'luxury': 'high'
    }
    
    # Từ điển map accommodation type sang OSM tourism tags
    type_map = {
        'homestay': 'guest_house',
        'nhà nghỉ': 'guest_house',
        'khách sạn': 'hotel',
        'hotel': 'hotel',
        'resort': 'resort',
        'villa': 'chalet',
        'biệt thự': 'chalet',
        'hostel': 'hostel',
        'ký túc xá': 'hostel'
    }
    
    # Từ điển map ambiance tags
    ambiance_map = {
        'yên tĩnh': 'quiet',
        'quiet': 'quiet',
        'peaceful': 'quiet',
        'sôi động': 'lively',
        'lively': 'lively',
        'vibrant': 'lively',
        'gần biển': 'beachfront',
        'beach': 'beachfront',
        'beachfront': 'beachfront',
        'view đẹp': 'scenic',
        'scenic': 'scenic',
        'gia đình': 'family',
        'family': 'family',
        'romantic': 'romantic',
        'lãng mạn': 'romantic'
    }
    
    # Normalize budget
    budget_tier = budget_map.get(budget_text.lower().strip(), 'medium')
    
    # Normalize type
    acc_type = type_map.get(type_text.lower().strip(), 'guest_house')
    
    # Normalize ambiance tags
    tags = []
    if ambiance_text and ambiance_text.strip():
        # Split bằng dấu phẩy hoặc space
        words = [w.strip() for w in ambiance_text.replace(',', ' ').split()]
        for word in words:
            tag = ambiance_map.get(word.lower())
            if tag and tag not in tags:
                tags.append(tag)
    
    return {
        'budget': budget_tier,
        'type': acc_type,
        'tags': tags
    }


# ============================================================================
# PATTERN 4: INTAKE INFORMATION (Build SearchRequest)
# ============================================================================

def build_search_request(geo_data: Dict, filters: Dict) -> Dict:
    """
    Tổng hợp tất cả thông tin thành SearchRequest object
    
    Args:
        geo_data: Dữ liệu địa lý từ geocoding
        filters: Filters đã được normalize
    
    Returns:
        Dict chứa đầy đủ thông tin để search
    """
    search_request = {
        'location_name': geo_data['name'],
        'lat': geo_data['lat'],
        'lon': geo_data['lon'],
        'budget': filters['budget'],
        'type': filters['type'],
        'tags': filters['tags'],
        'radius': 5000,  # 5km radius
        'max_results': 10
    }
    
    return search_request