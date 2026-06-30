#!/usr/bin/env python3

# ****************************************
# SUNNY TIMES - Sunrise, Sunset facts
# Author: James Alix
# Created: Aug 21, 2025 @ 13:35
# Modified: Jun 22, 2026 @ 14:45
# ****************************************
import csv
import logging
import math
from datetime import date, datetime, timedelta
from pathlib import Path
import ephem
from ephem import Observer

# ---------- Set up LOGGER
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) %(message)s')
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

    output_dir.mkdir(parents=True, exist_ok=True)

    # SET BASE INFORMATION FOR THE OBSERVER ---> 233 Liberty Ln, Harrisville RI:
    tdy = date.today()
    dt = datetime.now()
    logger.info(f"TDY: {tdy}")
    start_tdy = ephem.Date(f"{tdy.year}/{tdy.month}/{tdy.day} 01:00:00")
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

    # Compute length of daylight & solar noon:
    daylight: timedelta = local_sunset - local_sunrise
    tdy_daylight: str = format_timedelta_hms(daylight)
    transit_time = home.next_transit(sun)  # solar noon
    tran_time = ephem.localtime(transit_time)  # solar noon local time

    # Compute max elevation:
    max_alt_degrees = float(sun.alt) * 180 / ephem.pi
    max_alt_deg_2 = round(math.degrees(float(sun.alt)), 1)

    # Get the date of last solstice (horizon still 0º):
    next_solstice = ephem.next_solstice(start_tdy)
    last_solstice = ephem.previous_solstice(start_tdy)

    next = next_solstice.datetime()
    last = last_solstice.datetime()
    next_format = next.strftime("%B %d, %Y, %H:%M:%S")
    last_format = last.strftime("%B %d, %Y, %H:%M:%S")
    # logger.info(f"Next solstice: {next}")
    # logger.info(f"Last Solstice: {last}")

    next_sol_daylight = solstice_daylight(next, home)  # , daylight
    next_sol_daylight_diff = daylight - next_sol_daylight
    last_sol_daylight = solstice_daylight(last, home)
    last_sol_daylight_diff = last_sol_daylight - daylight
    # logger.info(f"Diff daylight last solstice: {last_sol_daylight_diff}")


    diff = format_timedelta_hms(next_sol_daylight_diff)
    # logger.info(f"daylight diff: {next_sol_daylight_diff}")
    diff1 = format_timedelta_hms(last_sol_daylight_diff)

    # Times for civil twilight:
    home.horizon = "-6"
    am_twilight = ephem.localtime(home.next_rising(sun, start=start_tdy))
    pm_twilight = ephem.localtime(home.next_setting(sun, start=start_tdy))

    home.date = sunrise
    home.horizon = "0"
    sun.compute(home)
    azimuth_rise = round(math.degrees(float(sun.az)), 1)
    home.date = sunset
    home.horizon = "0"
    sun.compute(home)
    azimuth_set = round(math.degrees(float(sun.az)), 1)

    # Retrieve info about Moon:
    moon.compute()
    moon_rise = home.next_rising(moon, start=start_tdy)
    current_phase = moon.phase
    full_moon = ephem.next_full_moon(start_tdy)
    new_moon = ephem.next_new_moon(start_tdy)

    # Get some sun info for mirror date:
    day_mirror = mirror_date_info(tdy)

    mirror_sunrise = home.next_rising(sun, start=day_mirror)
    local_mirror_sunrise = ephem.localtime(mirror_sunrise)
    home.date = mirror_sunrise
    sun.compute(home)
    mirror_az = round(math.degrees(float(sun.az)), 1)

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
    next_ = "Next Solstice"
    lost = "Daylight Difference"
    last = "Last Solstice"
    lost1 = "Daylight Difference"
    moon_up = "Moon Rise"
    m_phase = "Current Moon Phase"
    next_full = "Next Full Moon"
    next_new = "Next New Moon"
    mirror_rise = "Sunrise @ mirror date"
    mirror_azimuth = "Azimuth @ mirror date"

    # Console text:
    results: str = f"""
===== Information for {date_today} =====

{first_light:.<24} {am_twilight.strftime("%H:%M:%S")}
{rise:.<24} {local_sunrise.strftime("%H:%M:%S")}
{az_rise:.<24} {azimuth_rise}
{set_:.<24} {local_sunset.strftime("%H:%M:%S")}
{az_set:.<24} {azimuth_set}
{last_light:.<24} {pm_twilight.strftime("%H:%M:%S")}

{solar_noon:.<24} {tran_time.strftime("%H:%M:%S")}
{max_elev:.<24} {max_alt_deg_2:.1f}º

{length:.<24} {tdy_daylight}

{next_:.<24} {next_format}
{lost:.<24} {diff}
{last:.<24} {last_format}
{lost1:.<24} {diff1}

{moon_up:.<24} {ephem.localtime(moon_rise).strftime("%H:%M:%S")}
{m_phase:.<24}  {current_phase:.2f}%
{next_full:.<24} {ephem.localtime(full_moon).strftime("%a, %b %d %Y @ %H:%M")}
{next_new:.<24} {ephem.localtime(new_moon).strftime("%a, %b %d %Y @ %H:%M")}

****************************************

Mirror Date is →  {day_mirror.strftime("%a, %b %d, %Y")}

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
        "Mirror Date": day_mirror,
    }
    # ****************************************

    # Print to console:
    print()
    print(results)
    print()

    # Print to text file:
    with open(txt_file_path, "w", encoding="utf-8") as file:
        file.write(results + "\n")
    logger.debug(
        f"Modified date for text file is: {datetime.fromtimestamp(txt_file_path.stat().st_mtime)}"
    )
    logger.debug(
        f"Txt wkday: {datetime.fromtimestamp(txt_file_path.stat().st_mtime).isoweekday()}"
    )

    # Print to csv file:
    file_exists = csv_file_path.exists()

    day_num = dt.isoweekday()
    csv_mod = datetime.fromtimestamp(csv_file_path.stat().st_mtime)
    # csv_mod_dt = datetime.fromtimestamp(csv_file_path.stat().st_mtime)
    mod_num = csv_mod.isoweekday()
    logger.info(f"csv modified date: {csv_mod}")
    logger.info(f"csv modified day number: {mod_num}")

    if file_exists and day_num == 2 and mod_num < day_num:
        with open(csv_file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_data.keys())
            if not file_exists:
                writer.writeheader()

            writer.writerow(csv_data)

        print(f"csv file has been updated on {csv_mod.strftime('%b %d %Y @ %H:%M:%S')}")
    else:
        print(f"The csv file already saved for this week \n(saved on {csv_mod.strftime('%b %d %Y @ %H:%M:%S')})")


# ****************************************

def mirror_date_info(tdy: date) -> date:
    next_solstice = ephem.next_solstice(tdy)

    next = next_solstice.datetime()
    next_date = next.date()

    diff = next_date - tdy
    mirror = next_date + diff
    return mirror


def solstice_daylight(next_solstice, home):
    solstice = ephem.Date(f"{next_solstice.year}/{next_solstice.month}/{next_solstice.day} 01:00:00")
    sol_ephem_date = ephem.Date(solstice)
    logger.info(f"Solstice daylight date: {sol_ephem_date}")
    sol_rise = ephem.localtime(home.next_rising(ephem.Sun(), start=sol_ephem_date))
    sol_set = ephem.localtime(home.next_setting(ephem.Sun(), start=sol_ephem_date))
    logger.info(f"Solstice rise: {sol_rise}; Sostice set: {sol_set}")
    solstice_len_daylight = sol_set - sol_rise
    logger.info(f"Daylight on solstice: {solstice_len_daylight}")
    return solstice_len_daylight


def format_timedelta_hms(td: timedelta) -> str:
    total_seconds = round(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d} hrs {minutes:02d} mins {seconds:02d} secs"


if __name__ == "__main__":
    main()
