import pandas as pd
import json
import requests
from bs4 import BeautifulSoup

site_html = requests.get('https://overwatch.blizzard.com/en-us/rates/').text
soup = BeautifulSoup(site_html, 'lxml')

param = soup.find_all(value=True) # All parameters for hero stats

def fetch_values(value_list, output_list, label, search_attr):
  for i in value_list:
    if i.parent.has_attr(search_attr) and i.parent[search_attr] == label:
      output_list.append(i['value'])

input_values = []
rq_values = []
tier_values = []
region_values = []
map_values = []

rq_dict = {}

#Fetch values for the parameters and put them into lists
fetch_values(param, input_values, "input", 'data-label')
fetch_values(param, rq_values, "rq", 'data-label')
fetch_values(param, tier_values, "tier", 'data-label')
fetch_values(param, region_values, "region", 'data-label')

#Fetch all map_values (they get a different one due to the html structure for the map dropdown)
for i in param:
  if i.parent.has_attr('data-label') and i.parent['data-label'] == "map": #Account for 'all-maps'
    map_values.append(i['value'])
  elif i.parent.parent.has_attr('data-label') and i.parent.parent['data-label'] == "map":
    map_values.append(i['value'])

#Fetch titles for game modes (just in case!)
for i in param:
  if i.parent.has_attr('data-label') and i.parent['data-label'] == "rq":
    rq_dict.update({i['value'] : i['data-title']})

params = {"input" : input_values[0], "map" : map_values[0], "region" : region_values[0], "role" : "All", "rq" : rq_values[1], "tier" : tier_values[0]}

#Change tier to "All" if Quick Play
if params["rq"] == "0":
  params.update({"tier" : "All"})

data = json.loads(requests.get("https://overwatch.blizzard.com/en-us/rates/data/", params=params).text)

df = pd.DataFrame(pd.json_normalize(data["rates"])).drop(columns=["id", "hero.portrait", "hero.name", "hero.color", "hero.roleIcon"]).rename(columns={"cells.name" : "Hero", "cells.pickrate" : "Pick rate", "cells.winrate" : "Win rate", "hero.role" : "Role"})
df[["Input", "Game Mode", "Tier", "Map", "Region"]] = [params["input"], rq_dict[params["rq"]], params["tier"], params["map"], params["region"]]

print(df)