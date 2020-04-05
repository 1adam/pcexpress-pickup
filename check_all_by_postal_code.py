import sys
import json
import requests
import haversine
from xml.dom.minidom import parseString
from datetime import datetime
from dateutil import tz
from haversine import haversine, Unit

from_zone = tz.gettz("UTC")
to_zone = tz.gettz("America/Toronto")

try:
  within_km = float(sys.argv[2])
except:
  within_km = float(5)

geo_url = "https://geocoder.ca/?geoit=xml&postal=" + sys.argv[1]
geo_data = requests.get(geo_url)
xmlData = parseString( geo_data.text )
pLat = float( xmlData.getElementsByTagName("latt")[0].firstChild.nodeValue )
pLong = float( xmlData.getElementsByTagName("longt")[0].firstChild.nodeValue )

myLatLong = ( pLat, pLong )

stores_to_check = []

with open('locations.json') as inf:
  all_locs = json.load(inf)

for loc in all_locs["locations"]:
  locLatLong = ( loc["geoPoint"]["latitude"], loc["geoPoint"]["longitude"] )
  if haversine(myLatLong, locLatLong) <= within_km:
    stores_to_check.append(loc)


def check_loblaws( store ):
    id = store["id"]

    # not entirely sure what this is for ("Colleague Testing")
    if "CT" in id:
      return

    address = store["address"]["formattedAddress"]
    storeBannerId = store["storeBannerId"]
    headers = {"Site-Banner": storeBannerId} # If this header isn't set, the site returns an error

#    print( f"Checking #{id} ({storeBannerId} @ {address} ..." )

    if storeBannerId == "loblaw":
      base_url = "https://www.loblaws.ca"

    if storeBannerId == "rcss" or storeBannerId == "superstore":
      base_url = "https://www.realcanadiansuperstore.ca"

    if storeBannerId == "nofrills":
      base_url = "https://www.nofrills.ca"

    if storeBannerId == "independentcitymarket":
      base_url = "https://www.independentcitymarket.ca"

    if storeBannerId == "wholesaleclub":
      base_url = "https://www.wholesaleclub.ca"

    # Using the base_url and headers, build the full URL
    url = f"{base_url}/api/pickup-locations/{id}/time-slots"
    # Make the HTTP request
    r = requests.get(url, headers=headers)
    # Use the builtin JSON decoder
    data = r.json()
    # We only want to process the timeSlots entries from the output
    try:
      timeslots = data["timeSlots"]
    except KeyError:
      print("Error - no timeSlots found, skipping")
      return

    # Initialze an empty string to store the pickup_times
    pickup_times = ""

    # Loop through the results
    for startTime in timeslots:
        # Get a list of pickup times where the "available" value is not False
        if not startTime.get("available") is False:
            # Convert the UTC times to local time
            start_time = local_time(startTime["startTime"])
            # Append the converted start_time to the results
            pickup_times += start_time
            pickup_times += "\n"

    if pickup_times:
        count = pickup_times.count("\n")
        output = f"{count} pickup times available at {storeBannerId} at {address}"
        output += "\n"
        output += pickup_times

        print(output)


# Convert the UTC timestamps to localtime
def local_time(timestamp):
    utc = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    utc = utc.replace(tzinfo=from_zone)
    local = utc.astimezone(to_zone)
    return str(local)


for tStore in stores_to_check:
  check_loblaws( tStore )