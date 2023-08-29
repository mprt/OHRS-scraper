#!/usr/bin/env python3

import requests
import re
import geopy
from geopy.distance import geodesic
from geopy.geocoders import Nominatim, ArcGIS
from prettytable import PrettyTable

# This script scrapes the OHRS system for available huts for a selected date.
# a bit like https://magazin.alpenverein.de/artikel/last-minute-huettenbuchung_5e154190-2c02-47a0-80fe-2cd4da0ba550#/
# but not just for the upcoming two days

START_DATE = "01.09.2023"
NIGHTS = 2  # max 14 nights
PERSONS = 2
HOME = "München, Germany" # Enter home address here
URL = "https://www.alpsonline.org/reservation"
MAX_ID = 700 # no idea, experimentally determined max value of hut_id
results = []

# WARNING: Parsing of the hut geolocations and calculation of the distance does
# not work good. Please don't rely on it.
# Also, the formats are pretty wild (UTM, CH1903) and geopy can't parse them
# properly
# Also I've most likely used it wrong.

geolocator = Nominatim(user_agent="OHRS-scraper")
location = geolocator.geocode(HOME)
print("Using Home Address: " + location.address)
home = (location.latitude, location.longitude)

session = requests.Session()

for hut_id in range(1, MAX_ID):

    # skip bad formatted data, maybe check manually later
    if hut_id in [446, 526, 607]: continue

    # parse the info block somehow...
    r = session.get(URL + f"/calendar?hut_id={hut_id}&lang=en")
    m = r.text.find('<div class="info">')
    n = r.text[m:].find('</div>') + m
    t = r.text[m:n]
    name = re.search(r'(?<=>).+(?=<)', t)[0]

    # check various "placeholders" for empty or non-available huts
    if f"Hut warden(s): </span>"   in t: continue # hut not found
    if f"Hut warden(s): -</span>"  in t: continue # hut not found
    if f"Hut warden(s): -----</span>"  in t: continue # hut not found
    if f"Hut warden(s): XX</span>" in t: continue # hut not found

    print(f"\r{hut_id:03}/{MAX_ID}, {name}{30*' '}", end="")

    # get JSON
    # this contains availability information for the 14 days after the START_DATE
    # the hut_id is selected by the previous request. hence we have to reuse the session cookie!
    r = session.get(URL + f"/selectDate?date={START_DATE}")#not necessary? , cookies = r.cookies)

    # number of nights with free beds for all persons
    freenights = 0

    # iterate over date range
    for j in range(NIGHTS):
        # iterate over available room classes
        # TODO: figure out room types
        for night in r.json()[f"{j}"]:
            if night["bedCategoryType"] != "ROOM": continue
            if night["freeRoom"] < PERSONS: continue
            freenights = freenights + 1
            break

    # we have found a matching hut!
    if freenights == NIGHTS:

        # parse some more data
        height = int(re.search(r'(?<=Height above sea level: )\d+', t)[0])
        coordinates = re.search(r'(?<=Coordinates: ).+(?=</)', t)[0]
        coordinates = coordinates.replace("’","'").replace("′","'").replace(",",".")

        try:
            # try to calculate the distance between HOME and the hut
            # this is probably rubbish!
            location = geopy.Point(coordinates)
            #location = ArcGIS().geocode(coordinates)
            distance = geodesic(home, location).km
        except (TypeError, ValueError) as e:
            # some coordinates are messed up and e.g. in CH1903 format. we ignore these
            distance = 999999

        results.append({"hut_id":hut_id,
                        "name":name,
                        "height":height,
                        "distance":round(distance,1),
                        "coordinates":coordinates})


# try to sort by distance
results.sort(key= lambda x:x["distance"])
table = PrettyTable()
table.field_names = ["ID", "Hut","Height [m]", "Distance [km]", "Coordinates"]
for r in results:
    table.add_row([r["hut_id"],r["name"],r["height"],r["distance"],r["coordinates"]])

with open("result.csv", 'w') as fp:
    fp.write(table.get_formatted_string("csv"))

print(table)
