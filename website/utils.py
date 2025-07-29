from datetime import timedelta, datetime
from typing import Tuple, Dict, Optional

# Define shelf life data for each produce type (in days)
PRODUCE_SHELF_LIFE = {
    "apple": {
        "refrigerated": 42,  # 6 weeks
        "room_temp": 7,
        "storage_tip": "Refrigerated: 4–6 weeks in the crisper drawer. Room Temperature: 5–7 days."
    },
    "banana": {
        "refrigerated": 7,  # Skin darkens but fruit stays fresh
        "room_temp": 7,
        "storage_tip": "Room Temperature: Up to 7 days in a cool, dark place. Refrigeration darkens skin but keeps fruit fresh longer."
    },
    "carrot": {
        "refrigerated": 28,  # 4 weeks
        "room_temp": 5,
        "storage_tip": "Refrigerated: 3–5 weeks in a plastic bag in the crisper drawer."
    },
    "cucumber": {
        "refrigerated": 10,  # 1-2 weeks
        "room_temp": 7,
        "storage_tip": "Refrigerated: 7–14 days, wrapped in paper towels and stored in a plastic bag."
    },
    "mango": {
        "refrigerated": 7,
        "room_temp": 5,
        "storage_tip": "Ripe (Refrigerated): 5–7 days. Ripe (Room Temperature): 2–5 days."
    },
    "orange": {
        "refrigerated": 28,  # 4 weeks
        "room_temp": 14,
        "storage_tip": "Refrigerated: 3–4 weeks. Room Temperature: 10–14 days."
    },
    "pepper": {
        "refrigerated": 10,  # 10-14 days
        "room_temp": 5,
        "storage_tip": "Refrigerated: 5–14 days, depending on variety."
    },
    "potato": {
        "refrigerated": 14,  # Not recommended but added as a fallback
        "room_temp": 75,  # 2-3 months
        "storage_tip": "Room Temperature: 2–3 months in a cool, dark, well-ventilated place. Refrigeration not recommended."
    }
}

def get_produce_shelf_life(produce_name: str, storage_type: str = "refrigerated") -> Tuple[int, str]:
    """
    Get the shelf life in days and storage tip for a given produce
    
    Args:
        produce_name: The name of the produce (e.g., 'apple', 'banana')
        storage_type: Either 'refrigerated' or 'room_temp'
        
    Returns:
        Tuple of (shelf_life_days, storage_tip)
    """
    # Clean up produce name - remove 'fresh' or 'rotten' prefix, convert to lowercase
    clean_name = produce_name.lower()
    for prefix in ["fresh", "rotten"]:
        if clean_name.startswith(prefix):
            clean_name = clean_name[len(prefix):].strip()
    
    # Get shelf life data or use defaults
    produce_data = PRODUCE_SHELF_LIFE.get(clean_name, {
        "refrigerated": 7,  # Default 1 week if unknown
        "room_temp": 3,
        "storage_tip": "For best quality, keep refrigerated."
    })
    
    shelf_life_days = produce_data.get(storage_type, produce_data.get("refrigerated"))
    storage_tip = produce_data.get("storage_tip", "")
    
    return shelf_life_days, storage_tip

def calculate_expiry_date(produce_name: str, detection_date: datetime, 
                         storage_type: str = "refrigerated") -> Tuple[datetime, str]:
    """
    Calculate the expected expiry date for a detected produce
    
    Args:
        produce_name: The name of the produce
        detection_date: The date when the produce was scanned
        storage_type: Either 'refrigerated' or 'room_temp'
        
    Returns:
        Tuple of (expiry_date, storage_recommendation)
    """
    # Skip calculation for rotten produce
    if "rotten" in produce_name.lower():
        return None, "This produce is already rotten."

    # Get shelf life information    
    shelf_life_days, storage_tip = get_produce_shelf_life(produce_name, storage_type)
    
    # Calculate expiry date
    expiry_date = detection_date + timedelta(days=shelf_life_days)
    
    # Prepare storage recommendation
    storage_recommendation = f"{storage_tip} Expected to stay fresh until {expiry_date.strftime('%d %B %Y')}."
    
    return expiry_date, storage_recommendation 