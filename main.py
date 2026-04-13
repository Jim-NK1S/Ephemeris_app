#!/usr/bin/env python3

# ****************************************
# SUNNY TIMES - Sunrise, Sunset facts
# Author: James Alix
# Created: Aug 21, 2025 @ 13:35
# Modified: Apr 11, 2026 @ 11:49
# ****************************************
import csv
import logging
from pathlib import Path
from datetime import date, timedelta, datetime
import math
import ephem
from ephem import Observer

from testing import tdy_start

# ---------- Set up LOGGER
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s")
file_handler = logging.FileHandler("sunny_times.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# ----------------------------------------

# Path for output setup:
path: Path = Path.cwd().resolve()
output_dir: Path = path / "Sun_output"
txt_file_path: Path = output_dir / "ephemeris_info.txt"
csv_file_path: Path = output_dir / "daylight_info.csv"

# Compute the mirror date from today:
tdy = date.today()
summer_sol = date(2026, 6, 21)
diff = summer_sol - tdy
mirror = summer_sol + diff
tdy_mirror = ephem.Date(f'{mirror.year}/{mirror.month}/{mirror.day} 01:00:00')


def main():
    """Retrieves the time of sunrise and
    sunset and length of daylight for today,
    and computes the difference in amount of daylight
    from the last solstice to today"""

    output_dir.mkdir(parents=True, exist_ok=True)

    # SET BASE INFORMATION FOR THE OBSERVER --->
    # Coordinates are for home @ 233 Liberty Ln, Harrisville RI:
    start_tdy = ephem.Date(f'{tdy.year}/{tdy.month}/{tdy.day} 01:00:00')
    home: Observer = ephem.Observer()
    home.lat = "41.96247219"
    home.lon = "-71.677855830"
    home.elevation = 118  # in whole meters
    home.date = start_tdy
    sun = ephem.Sun()
    moon = ephem.Moon()

    # Retrieve sunrise and sunset times:
    sunrise = home.next_rising(sun, start=start_tdy)
    local_sunrise = ephem.localtime(sunrise)
    sunset = home.next_setting(sun, start=start_tdy)
    local_sunset = ephem.localtime(sunset)
    # Compute length of daylight:
    daylight: timedelta = local_sunset - local_sunrise
    tdy_daylight: str = format_timedelta_hms(daylight)
    transit_time = home.next_transit(sun)  # solar noon
    tran_time = ephem.localtime(transit_time)  # solar noon local time
    # Compute solar noon and max elevation:
    max_alt_degrees = float(sun.alt) * 180 / ephem.pi
    max_alt_deg_2 = round(math.degrees(float(sun.alt)), 1)
    # Get date of last solstice (horizon still 0º ):
    last_solstice = find_previous_solstice(tdy)
    sol_daylight: timedelta = get_daylight_diff(last_solstice[0], home)

    # Calculates difference in daylight between today and solstice:
    if last_solstice[1] == "summer":
        diff = format_timedelta_hms(sol_daylight - daylight)
    else:
        diff = format_timedelta_hms(daylight - sol_daylight)

    # Times for civil twilight:
    home.horizon = "-6"
    am_twilight = ephem.localtime(home.next_rising(sun, start=start_tdy))
    pm_twilight = ephem.localtime(home.next_setting(sun, start=start_tdy))

    home.date = sunrise
    home.horizon = "0"
    sun.compute(home)
    azimuth_rise = (round(math.degrees(float(sun.az)), 1))
    home.date = sunset
    home.horizon = "0"
    sun.compute(home)
    azimuth_set = (round(math.degrees(float(sun.az)), 1))

    # Retrieve info about Moon:
    moon_rise = home.next_rising(moon, start=start_tdy)
    full_moon = ephem.next_full_moon(start_tdy)
    new_moon = ephem.next_new_moon(start_tdy)

    # Get some sun info for mirror date:
    # home.date = tdy_mirror
    mirror_sunrise = home.next_rising(sun, start=tdy_mirror)
    local_mirror_sunrise = ephem.localtime(mirror_sunrise)
    home.date = mirror_sunrise
    sun.compute(home)
    mirror_az = (round(math.degrees(float(sun.az)), 1))
    mirror_alt = float(sun.alt) * 180 / ephem.pi

    # Set up variables for printing:
    date_today = tdy.strftime("%a, %b %d, %Y")
    first_light = "Civil Twilight"
    rise = "Sunrise"
    az_rise = "Azimuth @ sunrise"
    set_ = "Sunset"
    az_set = "Azimuth @ sunset"
    last_light = "Civil Twilight"
    length = "Length of Daylight"
    solar_noon = "Solar Noon"
    max_elev = "Max Sun Elevation"
    last = "Last Solstice"
    lost = "Daylight Difference"
    moon_up = "Moon Rise"
    next_full = "Next Full Moon"
    next_new = "Next New Moon"
    mirror_rise = "Sunrise @ mirror date"
    mirror_azimuth = "Azimuth @ mirror date"

    # Console text:
    results: str = f"""
Information for {date_today}

{first_light:.<24} {am_twilight.strftime("%H:%M:%S")}
{rise:.<24} {local_sunrise.strftime("%H:%M:%S")}
{az_rise:.<24} {azimuth_rise}
{set_:.<24} {local_sunset.strftime("%H:%M:%S")}
{az_set:.<24} {azimuth_set}
{last_light:.<24} {pm_twilight.strftime("%H:%M:%S")}

{solar_noon:.<24} {tran_time.strftime("%H:%M:%S")}
{max_elev:.<24} {max_alt_deg_2:.1f}º

{length:.<24} {tdy_daylight}

{last:.<24} {last_solstice[0].strftime("%a, %b %d @ %H:%M")}
{lost:.<24} {diff}

{moon_up:.<24} {ephem.localtime(moon_rise).strftime("%H:%M:%S")}
{next_full:.<24} {ephem.localtime(full_moon).strftime("%a, %b %d %Y @ %H:%M")}
{next_new:.<24} {ephem.localtime(new_moon).strftime("%a, %b %d %Y @ %H:%M")}

****************************************

Mirror Date is →  {mirror.strftime("%a, %b %d, %Y")}

{mirror_rise:.<24} {local_mirror_sunrise.strftime("%H:%M:%S")}
{mirror_azimuth:.<24} {mirror_az}

""".strip()

    csv_data = {
        "Date": date.today(),
        "Sunrise": local_sunrise.strftime("%H:%M:%S"),
        "Azimuth @ Sunrise": azimuth_rise,
        "Sunset": local_sunset.strftime("%H:%M:%S"),
        "Azimuth @ Sunset": azimuth_set,
        "Diff from Solstice": diff,
        "Solar Noon": tran_time.strftime("%H:%M:%S"),
        "Sun Elevation": round(max_alt_degrees, 2),
        "Length of Daylight": tdy_daylight,
        "Mirror Date": mirror,
    }
    # ****************************************

    # Print to console:
    print()
    print(results)
    print()

    # Print to text file:
    with open(txt_file_path, "w", encoding="utf-8") as file:
        file.write(results + "\n")
    logger.info(f"Modified date for text file is: {datetime.fromtimestamp(txt_file_path.stat().st_mtime)}")
    logger.info(f'Txt wkday: {datetime.fromtimestamp(txt_file_path.stat().st_mtime).isoweekday()}')

    # Print to csv file:
    file_exists = csv_file_path.exists()

    tdy_wk_num = tdy.isocalendar()[1]
    csv_mod = date.fromtimestamp(csv_file_path.stat().st_mtime)
    csv_mod_wkday_num = csv_mod.isoweekday()

    logger.info(f"Modified date for csv file is: {datetime.fromtimestamp(csv_file_path.stat().st_mtime)}")
    logger.info(f'Txt wkday: {datetime.fromtimestamp(csv_file_path.stat().st_mtime).isoweekday()}')

    if file_exists and csv_mod_wkday_num != 1 and csv_mod < tdy:
         with open(csv_file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_data.keys())
            if not file_exists:
                writer.writeheader()

            writer.writerow(csv_data)

         print("csv file has been updated at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        print("The csv file already exists for this week.")

# ****************************************

def find_previous_solstice(given_date: date) -> tuple:
    """
    Finds the most recent solstice before given_date.
    """
    prev_summer = None
    prev_winter = None

    try:
        prev_summer = ephem.previous_summer_solstice(tdy_start)
    except Exception as e:
        logger.warning("Could not determine previous summer solstice: %s", e)

    try:
        prev_winter = ephem.previous_winter_solstice(tdy_start)
    except Exception as e:
        logger.warning("Could not determine previous winter solstice: %s", e)

    if prev_summer and prev_winter:
        if prev_summer > prev_winter:
            return prev_summer.datetime(), "summer"
        return prev_winter.datetime(), "winter"
    elif prev_summer:
        return prev_summer.datetime(), "summer"
    elif prev_winter:
        return prev_winter.datetime(), "winter"
    else:
        raise RuntimeError("Can't find any solstice")


def get_daylight_diff(sol_date: date, home):
    sol_rise = ephem.localtime(home.previous_rising(ephem.Sun(), start=sol_date))
    sol_set = ephem.localtime(home.next_setting(ephem.Sun(), start=sol_date))
    daylight = sol_set - sol_rise

    logger.info(f"sol_date: {sol_date}")
    logger.info(f"Sol_rise: {sol_rise}; sol_set: {sol_set}; daylight: {daylight}")
    return daylight


def format_timedelta_hms(td: timedelta) -> str:
    total_seconds = round(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d} hrs {minutes:02d} mins {seconds:02d} secs"


if __name__ == "__main__":
    # tdy = date.today()
    # if csv_file_path.exists():
    #     if date.fromtimestamp(csv_file_path.stat().st_mtime) < tdy:
    #         main()
    #     else:
    #         print("\n\nYOU'VE ALREADY RUN THE SCRIPT TODAY !!! \n")
    # else:
    main()
