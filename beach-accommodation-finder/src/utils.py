"""
Helper functions - Các hàm tiện ích
"""

import math
from typing import Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Tính khoảng cách giữa 2 tọa độ GPS bằng công thức Haversine
    
    Args:
        lat1, lon1: Tọa độ điểm 1
        lat2, lon2: Tọa độ điểm 2
    
    Returns:
        Khoảng cách tính bằng kilometers
    """
    # Chuyển độ sang radian
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Công thức Haversine
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Bán kính Trái Đất (km)
    radius = 6371
    
    return radius * c


def format_distance(distance_km: float) -> str:
    """
    Format khoảng cách để hiển thị
    
    Args:
        distance_km: Khoảng cách tính bằng km
    
    Returns:
        String đã format (vd: "2.5 km" hoặc "850 m")
    """
    if distance_km < 1:
        return f"{int(distance_km * 1000)} m"
    return f"{distance_km:.1f} km"


def safe_get(dictionary: dict, key: str, default=None):
    """
    Lấy giá trị từ dict một cách an toàn
    
    Args:
        dictionary: Dict cần lấy giá trị
        key: Key cần tìm
        default: Giá trị mặc định nếu không tìm thấy
    
    Returns:
        Giá trị hoặc default
    """
    try:
        return dictionary.get(key, default)
    except:
        return default