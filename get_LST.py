import requests
from skyfield.api import load, wgs84
from datetime import datetime, timezone

# Get approximate location from IP
def get_my_location():
    response = requests.get("https://ipinfo.io/json")
    loc = response.json()['loc'].split(',')
    return float(loc[0]), float(loc[1])

# Convert decimal hours to hh:mm:ss
def decimal_hours_to_hms(decimal_hours):
    total_seconds = decimal_hours * 3600
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    return hours, minutes, seconds

lat, lon = get_my_location()

# Load ephemeris and timescale
eph = load('de421.bsp')
ts = load.timescale()

# Observer location
observer = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)

# Get current time in UTC
now = datetime.now(timezone.utc)
t = ts.from_datetime(now)

# Greenwich Apparent Sidereal Time (GAST)
gast = t.gast

# Local Sidereal Time (LST)
lst_decimal = (gast + lon / 15.0) % 24
h, m, s = decimal_hours_to_hms(lst_decimal)

# Output
print(f"Your approximate location: {lat:.4f}°, {lon:.4f}°")
print(f"Local Sidereal Time: {lst_decimal:.6f} hours")
print(f"LST formatted: {h:02d}:{m:02d}:{s:05.2f}")

