# Start_Observation.py

import csv
import threading
import time
import os
import sys
from datetime import datetime, timedelta
from astropy.time import Time
from astropy.coordinates import Angle

stop_event = threading.Event()

class QuitProgram(Exception):
    pass

# 1. Read lat/lon from location.dat
def get_location():
    with open("location.dat", "r") as f:
        lat, lon = map(float, open("location.dat").readline().strip().split(","))
    return lat, lon

# 2. Read entire InterferometerWorkbook.csv
def read_workbook():
    with open("InterferometerWorkbook.csv", newline='') as csvfile:
        rows = list(csv.reader(csvfile))
    return rows

# 3. Check if RA column is in ascending order from line 4 onward
def check_ra_order(rows):
    ra_vals = []
    for row in rows[3:]:
        try:
            ra_str = row[1].strip()
            ra = Angle(ra_str, unit='hourangle').hour
            ra_vals.append(ra)
        except:
            continue
    return all(earlier <= later for earlier, later in zip(ra_vals, ra_vals[1:]))

# Convert RA string to hours
def ra_str_to_hours(ra_str):
    return Angle(ra_str, unit='hourangle').hour

# Calculate frequency from 21cm line and recession velocity (Kps)
def calculate_frequency(velocity_kps):
    c = 299792.458  # km/s
    rest_freq = 1420.405751  # MHz
    return rest_freq * (1 - (velocity_kps / c))

# Get current LST from lat/lon
from astropy.coordinates import EarthLocation

def get_current_lst(lat, lon):
    location = EarthLocation(lat=lat, lon=lon)
    t = Time.now()
    return t.sidereal_time('mean', longitude=location.lon).hour

# Update workbook with date/time for observation
def update_observation(rows, idx):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows[idx][5] = now_str
    with open("InterferometerWorkbook.csv", "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)

# Main Scheduler Loop

def start_observation():
    lat, lon = get_location()
    rows = read_workbook()
    SIDEREAL_CORRECTION = 1.0027379
    print("[INFO] Latitude and Longitude read in")
    if not check_ra_order(rows):
        print("RA values in InterferometerWorkbook.csv must be in ascending order. Please correct and rerun.")
        return
    print("[INFO] InterferometerWorkbook.csv is in correct order.")
    while True:
        lst = get_current_lst(lat, lon)
        print(f"[DEBUG] Current LST: {lst:.4f}")
        print(f"[DEBUG] Current wall time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        found_target = False
        for i, row in enumerate(rows[3:], start=3):
            if row[5].strip():
                continue
            print("[DEBUG] In enummerate loop.")
            try:
                ra = ra_str_to_hours(row[1])
                width_arcmin = float(row[3])
                velocity_kps = float(row[4])
                print(f"[DEBUG] Row {i}: {row}")
                print(f"[DEBUG] Target RA: {ra:.4f}, Current LST: {lst:.4f}")

            except:
                continue
            print("[DEBUG] RA, width and velocity found.")
            if ra > lst + 5/60: # 5 second breathing space
                width_seconds = width_arcmin * 4
                buffer = 10  # seconds buffer
                start_ra = ra - (width_seconds + buffer) / 2 / 3600
                print("[MATCH] Preparing to observe.")
                print(f"[MATCH] Scheduling observation for {row[0]} at LST: {start_ra:.4f}, LST now: {lst:.4f}")
                delta_seconds = (start_ra - lst) * 3600
                if delta_seconds < 0:
                    print(f"[**SKIPPING**] Too late for this one: {row[0]}. Continuing on") 
                    continue  # missed this one
                delta_seconds = delta_seconds / SIDEREAL_CORRECTION
                delta_minutes = delta_seconds / 60
                delta_hours = delta_seconds / 3600
                print(f"[MATCH] Sleeping {delta_minutes:.2f} minutes until observation. Wait time = {delta_hours:.4f} hours")

                time.sleep(delta_seconds)

                freq = calculate_frequency(velocity_kps)
                samples = int((width_seconds + buffer) * 2e6)
                lst = get_current_lst(lat, lon)
                print(f"[**OBSERVING**] Observation begins. Frequency = {freq:.6f}e6, nsamples = {samples}.")
                print(f"[**OBSERVING**]                     lst = {lst:.4f}")
                # Dummy command placeholder -- replace with actual
                os.system(f'uhd_rx_cfile --args="type=usrp1,fpga=usrp1_fpga_4rx.rbf,rx_subdev_spec=A:B"  -r 2e6 --gain=40 --nsamples={samples} -f {freq:.6f}e6 RX_AB.dat')
                obj_dir = row[0].replace(" ", "_")
                os.makedirs(obj_dir, exist_ok=True)
                os.rename("RX_AB.dat", os.path.join(obj_dir, "RX_AB.dat"))
                # Write frequency to freq.dat
                freq_file_path = os.path.join(obj_dir, "freq.dat")
                with open(freq_file_path, "w") as f:
                    f.write(f"{freq:.6f}e6\n")
                update_observation(rows, i)
                found_target = True
                break

        if not found_target:
            pending_ras = []
            for j, row in enumerate(rows[3:], start=3):
                if not row[5].strip():
                    try:
                        ra = ra_str_to_hours(row[1])
                        pending_ras.append((j, ra))
                    except:
                        continue

            if not pending_ras:
                print("All observations complete.")
                break

            # Get earliest RA still pending
            earliest_idx, earliest_ra = min(pending_ras, key=lambda x: x[1])

            if earliest_ra < lst:
                print("\n[INFO] No more observations left for today.")
                print(f"The next observation is RA={earliest_ra:.2f}, which is earlier than current LST={lst:.2f}")
                print("Options:")
                print("  [1] Quit")
                print("  [2] Skip to tomorrow, 10 minutes before next target")
                print("Waiting 10 minutes for input...")

                def wait_for_input():
                    try:
                        user_input = input("Type 1 to quit, 2 to continue (Esc to quit): ").strip()
                        if user_input == "1" or user_input == "\x1b":  # '\x1b' is ESC key
                            print("Quitting immediately as requested.")
                            os._exit(0)  # Hard exit, no cleanup
                        elif user_input == "2":
                            print("Advancing to next day.")
                        else:
                            print("No valid input received; continuing by default.")
                    except EOFError:
                        pass

                input_thread = threading.Thread(target=wait_for_input)
                input_thread.daemon = True
                input_thread.start()
                input_thread.join(timeout=600)  # 10-minute wait

                # Recalculate sleep time
                now = datetime.now()
                hours_until_ra = (earliest_ra - lst + 24) % 24
                target_time = now + timedelta(hours=hours_until_ra) - timedelta(minutes=10)
                sleep_seconds = (target_time - now).total_seconds()
                print(f"[INFO] Sleeping {sleep_seconds:.1f} seconds until tomorrow's first observation.")
                time.sleep(max(sleep_seconds, 0))
            else:
                print("[INFO] No matching observation yet—retrying in 60 seconds.")
                if current_lst > ra + 0.01:
                    print(f"[DEBUG] Skipping: LST {lst:.4f} is past RA {ra:.4f}")
                    continue

                time.sleep(60)

if __name__ == "__main__":
    start_observation()
