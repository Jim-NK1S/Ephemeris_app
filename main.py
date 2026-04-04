#!/usr/bin/env python3

# ****************************************
# SUNNY TIMES - Sunrise, Sunset facts
# Author: James Alix
# Created: Aug 21, 2025 @ 13:35
# Modified: Apr 1, 2026 @ 16:39
# ****************************************
import csv
import logging
from pathlib import Path
from datetime import date, timedelta, datetime

import ephem
from ephem import Observer
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

# ---------- Set up LOGGER
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
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


def main():
    """Retrieves the time of sunrise and
    sunset and length of daylight for today,
    and computes the difference in amount of daylight
    from the last solstice to today"""

    # SET BASE INFORMATION FOR THE OBSERVER --->
    # Coordinates are for home @ 233 Liberty Ln, Harrisville RI:
    home: Observer = ephem.Observer()
    home.lat = "41.96247219"
    home.lon = "-71.677855830"
    home.elevation = 118  # in whole meters
    given_date = date.today()
    logger.info(f"Given date: {given_date}")
    sun = ephem.Sun()
    moon = ephem.Moon()

    # Retrieve sun info for today:
    sunrise = home.next_rising(sun, start=given_date)
    local_sunrise = ephem.localtime(sunrise)
    sunset = home.next_setting(sun, start=given_date)
    local_sunset = ephem.localtime(sunset)
    daylight: timedelta = local_sunset - local_sunrise
    given_date_daylight: str = format_timedelta_hms(daylight)
    logger.info(f"tdy_daylight {given_date_daylight}")
    transit_time = home.next_transit(sun)  # solar noon
    tran_time = ephem.localtime(transit_time)  # solar noon local time
    home.date = transit_time
    max_alt_degrees = float(sun.alt) * 180 / ephem.pi  # sun's elevation at solar noon
    logger.info(f"Max altitude: {max_alt_degrees:.2f} degrees")

    # Times for civil twilight:
    home.horizon = "-6"
    am_twilight = ephem.localtime(home.next_rising(sun, start=given_date))
    pm_twilight = ephem.localtime(home.next_setting(sun, start=given_date))

    # CALCULATE daylight lost or gained after the last solstice ==>
    # Reset horizon for actual sun rise/set:
    home.horizon = "0"
    last_solstice = find_previous_solstice(given_date)
    logger.info(f"Last solstice: {last_solstice}")

    # Retrieves length of daylight on last solstice:
    sol_daylight: timedelta = get_daylight_diff(last_solstice[0], home)

    # Calculates difference between today and solstice:
    if last_solstice[1] == "summer":
        diff = format_timedelta_hms(sol_daylight - daylight)
    else:
        diff = format_timedelta_hms(daylight - sol_daylight)

    # Retrieve info about Moon:
    moon_rise = home.next_rising(moon, start=given_date)
    full_moon = ephem.next_full_moon(given_date)
    new_moon = ephem.next_new_moon(given_date)

    logger.info(f"Last solstice 1: {last_solstice[1]}")
    logger.info(f"Last solstice 0: {last_solstice[0]}")
    logger.info(
        f"today_length: {sol_daylight}; solstice_length: {daylight}; diff: {diff}"
    )

    # Set up variables for printing:
    date_today = given_date.strftime("%a, %b %d, %Y")
    first_light = "Civil Twilight"
    rise = "Sunrise"
    set = "Sunset"
    last_light = "Civil Twilight"
    length = "Length of Daylight"
    solar_noon = "Solar Noon"
    max_elev = "Max Sun Elevation"
    last = "Last Solstice"
    lost = "Daylight Difference"
    moon_up = "Moon Rise"
    next_full = "Next Full Moon"
    next_new = "Next New Moon"

    # Console text:
    results: str = f"""[info]
    Information for {date_today} \n
    {first_light:.<24} {am_twilight.strftime("%H:%M:%S")}
    {rise:.<24} {local_sunrise.strftime("%H:%M:%S")}
    {set:.<24} {local_sunset.strftime("%H:%M:%S")}
    {last_light:.<24} {pm_twilight.strftime("%H:%M:%S")}\n
    {solar_noon:.<24} {tran_time.strftime("%H:%M:%S")}
    {max_elev:.<24} {max_alt_degrees:.2f}º\n
    {length:.<24} {given_date_daylight} \n
    {last:.<24} {last_solstice[0].strftime("%a, %b %d @ %H:%M")} \n
    {lost:.<24} {diff} \n
    ****************************************

    {moon_up:.<24} {ephem.localtime(moon_rise).strftime("%H:%M:%S")}
    {next_full:.<24} {ephem.localtime(full_moon).strftime("%a, %b %d %Y @ %H:%M")}
    {next_new:.<24} {ephem.localtime(new_moon).strftime("%a, %b %d %Y @ %H:%M")}  [/info]
    """

    csv_data = {
        "Date": date.today(),
        "Sunrise": local_sunrise.strftime("%H:%M:%S"),
        "Sunset": local_sunset.strftime("%H:%M:%S"),
        "Diff from Solstice": diff,
        "Solar Noon": tran_time.strftime("%H:%M:%S"),
        "Sun Elevation": round(max_alt_degrees, 2),
        "Length of Daylight": given_date_daylight,
    }
    # ****************************************

    # Print to console:
    custom_theme = Theme(
        {"info": "gold1", "danger": "magenta2 italic", "success": "green"}
    )
    console = Console(theme=custom_theme)

    print()
    print()
    console.print(
        Panel.fit(
            results,
            title="Daily Ephemeris Information",
            border_style="red",
            title_align="left",
        )
    )

    # Print to text file:
    with open(txt_file_path, "w") as file:
        file.write(results)

    # Print to csv file:
    file_exists = csv_file_path.exists()
    with open(csv_file_path, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_data.keys())
        if not file_exists:
            writer.writeheader()

        writer.writerow(csv_data)


# ****************************************

def find_previous_solstice(given_date: date) -> tuple:
    """
    Simplified version that finds the most recent solstice before given_date.
    """
    # Start from the given date and work backwards
    current_date = ephem.Date(given_date)

    # Find the previous summer solstice
    try:
        prev_summer = ephem.previous_summer_solstice(given_date)
    except Exception as e:
        print(e)

    # Find the previous winter solstice
    try:
        prev_winter = ephem.previous_winter_solstice(current_date)
    except Exception as e:
        print(e)

    # Return the more recent one
    if prev_summer and prev_winter:
        if prev_summer > prev_winter:
            return prev_summer.datetime(), "summer"
        else:
            return prev_winter.datetime(), "winter"
    elif prev_summer:
        return prev_summer.datetime(), "summer"
    elif prev_winter:
        return prev_winter.datetime(), "winter"
    else:
        return ("Can't find any solstice",)


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
    if date.fromtimestamp(csv_file_path.stat().st_mtime) < date.today():
        main()
    else:
        print("\n\nYOU'VE ALREADY RUN THE SCRIPT TODAY !!! \n")
