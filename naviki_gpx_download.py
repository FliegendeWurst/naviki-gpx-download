from bs4 import BeautifulSoup
import requests
import time
import re
import pathlib

# set this to your token (open naviki.org, login, copy the value of the Authorization header in the browser dev tools)
oauth_token = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
# (optional) select which routes to export
route_types = "routedAll,recordedMy,recordedOthers"
# GPX files will be saved in this directory
output_dir = pathlib.Path("/tmp")
title_pattern = r'(?P<day>\d\d).(?P<month>\d\d).(?P<year>\d\d), (?P<hour>\d\d):(?P<minute>\d\d)'
century = "20"
timestamp = str(int(time.time()))

s = requests.Session()
s.headers.update({'Authorization': f'Bearer {oauth_token}'})
s.headers.update({'Accept': 'application/json'})

more_to_download = True
offset = 0

while more_to_download:
    r = s.get(f'https://www.naviki.org/naviki/api/v6/Way/2/findUserWaysByFilter/?filter={route_types}&sort=crdateDesc&offset={offset}&fullDataSet=0&_={timestamp}')
    j = r.json()
    more_to_download = len(j["ways"]) > 0
    offset += len(j["ways"])
    for way in j["ways"]:
        uuid = way["uuid"]
        title = way["title"]
        print(title, uuid)
        m = re.search(title_pattern, title)
        if m is None:
            print("failed to extract time from title!")
            # it is possible to extract the time from way["crdate"]
            # datetime.utcfromtimestamp(way["crdate"]).strftime("%Y-%m-%d_%H-%M")
            # but this requires knowing the time zone!
            # which is not returned by the API
            more_to_download = False # exit outer loop
            break
        new_title = century + m.group("year") + "-" + m.group("month") + "-" + m.group("day")
        new_title += "_" + m.group("hour") + "-" + m.group("minute")
        new_title += "_Naviki.gpx"
        form_data = {
            "wayUuid": uuid,
            "oauth_token": oauth_token,
            "format": "gpx"
        }
        dl_headers = {
            "Authorization": None # token is passed in form data
        }
        dl = s.post('https://www.naviki.org/naviki/api/v6/Util/wayToFileWithUser/',
                    data=form_data,
                    headers=dl_headers)
        if not dl.text.startswith("<?xml"):
            print("failed to download GPX!")
            more_to_download = False # exit outer loop
            break
        save_path = output_dir.joinpath(new_title)
        with open(save_path, "wb") as f:
            print("saving", save_path)
            f.write(dl.text.encode())
