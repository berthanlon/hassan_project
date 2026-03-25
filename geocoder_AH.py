"""
geocoder.py
-----------
Handles UK postcode geocoding using the free postcodes.io API.
"""

import requests

API_BASE = "https://api.postcodes.io/postcodes"


def is_valid_format(postcode):
    """
    Very permissive check — just makes sure the input is non-empty
    and roughly the right length. The API will reject anything invalid.
    Accepts with or without spaces, upper or lowercase.
    """
    cleaned = postcode.strip().replace(" ", "")
    # UK postcodes without space are 5-7 characters
    if len(cleaned) < 5 or len(cleaned) > 7:
        return False
    # Must start with at least one letter
    if not cleaned[0].isalpha():
        return False
    return True


def geocode(postcode):
    """
    Look up a UK postcode via postcodes.io API.
    Returns a dict with postcode, lat, lng, district, ward.
    Returns None if not found or on network error.
    """
    clean = postcode.strip().replace(" ", "").upper()
    try:
        url = API_BASE + "/" + clean
        response = requests.get(url, timeout=8)
        data = response.json()

        if data.get("status") == 200:
            result = data["result"]
            return {
                "postcode": result["postcode"],
                "lat":      result["latitude"],
                "lng":      result["longitude"],
                "district": result.get("admin_district") or "",
                "ward":     result.get("admin_ward") or "",
            }
        else:
            return None

    except Exception as e:
        print("Geocode error:", e)
        return None


def bulk_geocode(postcodes):
    """
    Geocode multiple postcodes in one API call (up to 100).
    Returns a list of result dicts (None for each not found).
    """
    clean = [p.strip().replace(" ", "").upper() for p in postcodes]
    try:
        response = requests.post(
            API_BASE,
            json={"postcodes": clean},
            timeout=10
        )
        data = response.json()

        if data.get("status") == 200:
            results = []
            for item in data["result"]:
                r = item.get("result")
                if r:
                    results.append({
                        "postcode": r["postcode"],
                        "lat":      r["latitude"],
                        "lng":      r["longitude"],
                        "district": r.get("admin_district") or "",
                        "ward":     r.get("admin_ward") or "",
                    })
                else:
                    results.append(None)
            return results

    except Exception as e:
        print("Bulk geocode error:", e)

    return [None] * len(postcodes)