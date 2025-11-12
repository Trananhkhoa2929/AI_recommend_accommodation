"""
GIAI ĐOẠN 4: Backend Execution & Ranking
Bao gồm: Searching, Normalize Output, Filter, Ranking
"""

import requests
import time
from typing import List, Dict, Optional, Tuple
from .utils import haversine_distance


# ============================================================================
# PATTERN 5: SEARCHING (OpenStreetMap Overpass API) - CẢI TIẾN
# ============================================================================

def search_accommodations(search_request: Dict) -> Tuple[Optional[List], Optional[str]]:
    """
    Tìm kiếm nơi ở bằng OpenStreetMap Overpass API với retry và fallback
    
    Args:
        search_request: Dict chứa thông tin tìm kiếm
    
    Returns:
        Tuple (osm_elements, error_message)
    """
    # Extract parameters
    lat = search_request['lat']
    lon = search_request['lon']
    acc_type = search_request['type']
    radius = search_request['radius']
    
    # Danh sách các Overpass API servers (để fallback)
    overpass_servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter"
    ]
    
    # Thử với nhiều loại tourism tags (mở rộng tìm kiếm)
    tourism_types = [acc_type, 'hotel', 'guest_house', 'apartment', 'hostel']
    
    # Xây dựng query tối ưu hơn (ngắn gọn, timeout 20s)
    query = f"""
    [out:json][timeout:20];
    (
      node["tourism"~"^({"|".join(tourism_types)})$"](around:{radius},{lat},{lon});
      way["tourism"~"^({"|".join(tourism_types)})$"](around:{radius},{lat},{lon});
    );
    out body 50;
    """
    
    last_error = None
    
    # Thử với từng server
    for server_url in overpass_servers:
        try:
            # Gọi API với timeout 25s
            response = requests.post(
                server_url, 
                data={'data': query}, 
                timeout=25,
                headers={'User-Agent': 'BeachAccommodationFinder/1.0'}
            )
            
            # Kiểm tra status code
            if response.status_code == 200:
                data = response.json()
                
                # Kiểm tra có elements không
                if 'elements' in data and len(data['elements']) > 0:
                    return data['elements'], None
                else:
                    # Không có kết quả từ server này, thử server khác
                    last_error = f"Server {server_url.split('/')[2]} không trả về kết quả"
                    continue
            
            elif response.status_code == 504 or response.status_code == 429:
                # Gateway timeout hoặc rate limit, thử server khác
                last_error = f"Server {server_url.split('/')[2]} quá tải (HTTP {response.status_code})"
                time.sleep(2)  # Đợi 2s trước khi thử server khác
                continue
            
            else:
                last_error = f"Server {server_url.split('/')[2]} trả về lỗi HTTP {response.status_code}"
                continue
                
        except requests.exceptions.Timeout:
            last_error = f"Server {server_url.split('/')[2]} timeout"
            continue
        
        except requests.exceptions.RequestException as e:
            last_error = f"Lỗi kết nối {server_url.split('/')[2]}: {str(e)}"
            continue
        
        except Exception as e:
            last_error = f"Lỗi không xác định: {str(e)}"
            continue
    
    # Nếu tất cả servers đều thất bại
    return None, f"Không thể kết nối Overpass API. Lỗi cuối: {last_error}"


# ============================================================================
# FALLBACK: TÌM KIẾM BẰNG NOMINATIM (Khi Overpass fail)
# ============================================================================

def search_accommodations_nominatim_fallback(search_request: Dict) -> Tuple[Optional[List], Optional[str]]:
    """
    Tìm kiếm bằng Nominatim API (đơn giản hơn, ít kết quả hơn)
    
    Args:
        search_request: Dict chứa thông tin tìm kiếm
    
    Returns:
        Tuple (elements, error_message)
    """
    try:
        lat = search_request['lat']
        lon = search_request['lon']
        location_name = search_request['location_name']
        
        # Tìm kiếm hotels/accommodations gần địa điểm
        url = "https://nominatim.openstreetmap.org/search"
        
        params = {
            'q': f"hotel {location_name}",
            'format': 'json',
            'limit': 20,
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'BeachAccommodationFinder/1.0'
        }
        
        time.sleep(1)  # Rate limit
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None, f"Nominatim fallback thất bại: HTTP {response.status_code}"
        
        data = response.json()
        
        if not data or len(data) == 0:
            return None, "Không tìm thấy kết quả"
        
        # Chuyển đổi sang format giống Overpass
        elements = []
        for item in data:
            if 'lat' in item and 'lon' in item:
                element = {
                    'id': int(item.get('place_id', 0)),
                    'type': 'node',
                    'lat': float(item['lat']),
                    'lon': float(item['lon']),
                    'tags': {
                        'name': item.get('display_name', 'Unnamed'),
                        'tourism': 'hotel'
                    }
                }
                elements.append(element)
        
        return elements, None
        
    except Exception as e:
        return None, f"Lỗi Nominatim fallback: {str(e)}"


# ============================================================================
# PATTERN 6: NORMALIZE OUTPUT (OSM Data → Accommodation Objects)
# ============================================================================

def normalize_osm_data(osm_elements: List[Dict]) -> List[Dict]:
    """
    Chuyển đổi dữ liệu thô từ OSM sang cấu trúc Accommodation chuẩn
    
    Args:
        osm_elements: List các elements từ OSM Overpass
    
    Returns:
        List các Accommodation objects (dạng dict)
    """
    accommodations = []
    seen_names = set()  # Để tránh duplicate
    
    for element in osm_elements:
        # Chỉ xử lý những element có tags
        if 'tags' not in element:
            continue
        
        tags = element['tags']
        
        # Extract name
        name = tags.get('name', tags.get('addr:street', 'Unnamed'))
        
        # Tránh duplicate
        if name in seen_names:
            continue
        
        # Extract coordinates
        # Với node thì có sẵn lat, lon
        # Với way thì cần tính center (đơn giản hóa: bỏ qua way không có lat/lon)
        if 'lat' not in element or 'lon' not in element:
            continue
        
        lat = element['lat']
        lon = element['lon']
        
        # Extract tourism type
        tourism_type = tags.get('tourism', 'accommodation')
        
        # Build tags list
        acc_tags = [tourism_type]
        
        # Thêm các tags khác nếu có
        if 'amenity' in tags:
            acc_tags.append(tags['amenity'])
        if 'building' in tags:
            acc_tags.append(tags['building'])
        
        # Xây dựng Accommodation object
        accommodation = {
            'id': element.get('id', 0),
            'name': name,
            'location': (lat, lon),
            'type': tourism_type,
            'tags': acc_tags,
            'score': 0.0,
            'distance': 0.0,
            'source': 'osm'
        }
        
        accommodations.append(accommodation)
        seen_names.add(name)
    
    return accommodations


# ============================================================================
# PATTERN 7: FILTER RESULTS
# ============================================================================

def filter_results(accommodations: List[Dict], search_request: Dict) -> List[Dict]:
    """
    Lọc các kết quả theo criteria
    
    Args:
        accommodations: List các Accommodation objects
        search_request: Search request chứa filters
    
    Returns:
        List các Accommodation đã lọc
    """
    filtered = []
    
    center_lat = search_request['lat']
    center_lon = search_request['lon']
    max_distance = search_request['radius'] / 1000  # Convert m sang km
    required_tags = search_request.get('tags', [])
    
    for acc in accommodations:
        # Tính khoảng cách
        acc_lat, acc_lon = acc['location']
        distance = haversine_distance(center_lat, center_lon, acc_lat, acc_lon)
        
        # Filter 1: Distance
        if distance > max_distance:
            continue
        
        # Filter 2: Tags (nếu có required tags)
        # Nếu không có required tags thì pass
        if required_tags:
            # Kiểm tra có ít nhất 1 tag khớp
            has_match = any(tag in acc['tags'] for tag in required_tags)
            if not has_match:
                continue
        
        # Pass all filters
        acc['distance'] = distance
        filtered.append(acc)
    
    return filtered


# ============================================================================
# PATTERN 8: RANKING
# ============================================================================

def rank_results(accommodations: List[Dict], search_request: Dict) -> List[Dict]:
    """
    Xếp hạng các kết quả theo score
    
    Args:
        accommodations: List các Accommodation đã lọc
        search_request: Search request để tính bonus
    
    Returns:
        List các Accommodation đã xếp hạng (top 5)
    """
    if not accommodations:
        return []
    
    required_tags = search_request.get('tags', [])
    
    for acc in accommodations:
        score = 10.0  # Base score
        
        # Component 1: Proximity score (càng gần càng cao)
        distance = acc['distance']
        proximity_score = max(0, 5 - distance)
        score += proximity_score
        
        # Component 2: Tag match score
        acc_tags = set(acc['tags'])
        required_tags_set = set(required_tags)
        tag_matches = len(acc_tags & required_tags_set)
        tag_score = tag_matches * 2
        score += tag_score
        
        # Component 3: Type bonus (nếu type chính xác khớp)
        if acc['type'] == search_request['type']:
            score += 3
        
        # Component 4: Name bonus (nếu có tên rõ ràng)
        if acc['name'] != 'Unnamed':
            score += 1
        
        # Gán score
        acc['score'] = round(score, 2)
    
    # Sort theo score giảm dần
    sorted_accs = sorted(accommodations, key=lambda x: x['score'], reverse=True)
    
    # Lấy top 5
    top_results = sorted_accs[:5]
    
    # Thêm rank
    for i, acc in enumerate(top_results):
        acc['rank'] = i + 1
    
    return top_results