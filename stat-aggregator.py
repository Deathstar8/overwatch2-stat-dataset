import pandas as pd
import json
import requests
from bs4 import BeautifulSoup

site_html = requests.get('https://overwatch.blizzard.com/en-us/rates/').text
soup = BeautifulSoup(site_html, 'lxml')

param = soup.find_all(value=True)
param_values = [x['value'] for x in param]

input_values = param_values[4:6]
rq_values = param_values[6:8]
tier_values = param_values[8:16]
map_values = param_values[16:48]
region_values = param_values[48:]

rq_dictionary = {"0" : "Quick Play - Role Queue", "2" : "Competitive - Role Queue"}

params = {"input" : input_values[0], "map" : map_values[0], "region" : region_values[0], "role" : "All", "rq" : rq_values[0], "tier" : tier_values[0]}

data = json.loads(requests.get("https://overwatch.blizzard.com/en-us/rates/data/", params=params).text)
df = pd.DataFrame(pd.json_normalize(data["rates"])).drop(columns=["id", "hero.portrait", "hero.name", "hero.color", "hero.roleIcon"]).rename(columns={"cells.name" : "Hero", "cells.pickrate" : "Pickrate", "hero.role" : "Role"})
df[["Input", "Game Mode", "Tier", "Map", "Region"]] = [params["input"], rq_dictionary[params["rq"]], params["tier"], params["map"], params["region"]]

print(df)