import time
import subprocess
from skyfield.api import Topos, load
from datetime import datetime
import pytz
import requests

# Load Skyfield data for time and location
planets = load('de421.bsp')
earth = planets['earth']
ts = load.timescale()

# Function to get my location
def get_my_location():
    response = requests.get("https://ipinfo.io/json")
    loc = response.json()['loc'].split(',')
    return float(loc[0]), float(loc[1])

    lat, lon = get_my_location()
    observer = Topos(latitude_degrees=lat, longitude_degrees=lon)  # define observer
    location = earth + observer  # create location from earth + observer

# Now you can get longitude_hours from observer
    longitude_hours = observer.longitude.degrees / 15.0

# Function to calculate Local Sidereal Time (LST) at a given time
def calculate_lst(location):
    observer_time = datetime.utcnow().replace(tzinfo=pytz.utc)
    t = ts.utc(observer_time.year, observer_time.month, observer_time.day,
               observer_time.hour, observer_time.minute, observer_time.second)

    longitude_hours = location.longitude.degrees / 15.0
    gst_hours = t.gmst  # use correct skyfield call for GMST
    
    lst_hours = (gst_hours + longitude_hours) % 24

    # convert decimal hours to h, m, s
    total_seconds = lst_hours * 3600
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60

    print(f"LST (decimal): {lst_hours:.6f} hours")
    print(f"LST (hms): {hours:02d}:{minutes:02d}:{seconds:05.2f}")

    return lst_hours


# Read the target from the CSV file
def get_next_target():
    with open('InterferometerWorkbook.csv', 'r') as file:
        # Skip headers
        for _ in range(3):
            file.readline()
        line = file.readline().strip()
        # Split on commas, then strip whitespace from each field
        fields = [field.strip() for field in line.split(',')]
        return fields

# Prepare observation parameters and scripts
def prepare_and_schedule_observation(target_data, location):
    lst = calculate_lst(location)
    name, ra, dec, width, velocity, *rest = target_data
    
    width = float(width)
    velocity = float(velocity)
    
    frequency = 1420e6 + velocity * 1e3  # velocity in m/s offset example
    
    lst = calculate_lst(location)
    start_time = lst - (width / 120)  # width in arcminutes, divided by 2
    start_time = max(start_time, 0)
    
    duration = (width / 60) + 5
    nsamples = int(duration * 1e6)
    
    prepare_command = f"./prepare_next_target.sh {name} {ra} {dec} {start_time} {duration} {frequency} {nsamples}"
    subprocess.call(prepare_command, shell=True)
    
    run_command = f"./run_observation.sh {name} {frequency} {nsamples}"
    subprocess.call(run_command, shell=True)
    
    update_observation_date(name)

# Function to update observation date in the CSV file
def update_observation_date(name):
    with open('InterferometerWorkbook.csv', 'r') as file:
        lines = file.readlines()
    
    with open('InterferometerWorkbook.csv', 'w') as file:
        for line in lines:
            if name in line:
                # Replace the date field with the current UTC time
                file.write(line.strip() + f",{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n")
            else:
                file.write(line)

# Scheduler loop to keep checking and updating
def run_scheduler():
    lat, lon = get_my_location()
    location = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)

    while True:
        target_data = get_next_target()
        if target_data:
            prepare_and_schedule_observation(target_data, location)
        time.sleep(3600) # Check every hour (for example)

if __name__ == '__main__':
    run_scheduler()

