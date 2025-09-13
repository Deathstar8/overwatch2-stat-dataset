import pandas as pd
import json
import requests
import itertools
from bs4 import BeautifulSoup
from datetime import datetime

site_html = requests.get('https://overwatch.blizzard.com/en-us/rates/').text
soup = BeautifulSoup(site_html, 'lxml')

param = soup.find_all(value=True) # All parameters for hero stats

def fetch_values(value_list, output_list, label, search_attr):
  for i in value_list:
    if i.parent.has_attr(search_attr) and i.parent[search_attr] == label:
      output_list.append(i['value'])
    elif i.parent.parent.has_attr(search_attr) and i.parent.parent[search_attr] == label: #For fetching map values
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
fetch_values(param, map_values, "map", 'data-label')

#Fetch titles for game modes (just in case!) and put them in a dictionary
for i in param:
  if i.parent.has_attr('data-label') and i.parent['data-label'] == "rq":
    rq_dict.update({i['value'] : i['data-title']})

input_combos = list(itertools.product(input_values, rq_values, tier_values, region_values, map_values))

def get_data():
  params = {"input" : input_values[1], "map" : map_values[0], "region" : region_values[2], "role" : "All", "rq" : rq_values[1], "tier" : tier_values[3]}

  data_request = requests.get("https://overwatch.blizzard.com/en-us/rates/data/", params=params)
  if data_request.status_code != 200 and data_request.status_code == 404:
    print("Error! Data not found!")
  elif data_request.status_code != 200:
    print("Warning, encountered unexpected status code: " + data_request.status_code)

  data = json.loads(data_request.text)

  #Check if loaded data params matches input params
  #If they don't match, it probably means the input params were invalid (like fetching winrates based on competitive rank, but selecting Quick Play)
  if data['selected'] != params:
    print("Warning: Fetched data has different parameters than input parameters. Fetched data is most likely not reflective of input parameters.")
    print("Input parameters: " + str(params))
    print("Recieved (selected by website) parameters: " + str(data['selected']))

  df = pd.DataFrame(pd.json_normalize(data["rates"])).drop(columns=["id", "hero.portrait", "hero.name", "hero.color", "hero.roleIcon"]).rename(columns={"cells.name" : "Hero", "cells.pickrate" : "Pick rate", "cells.winrate" : "Win rate", "hero.role" : "Role"})
  df[["Input", "Game Mode", "Tier", "Map", "Region", "Timestamp"]] = [data['selected']["input"], rq_dict[data['selected']["rq"]], data['selected']["tier"], data['selected']["map"], data['selected']["region"], datetime.now().astimezone().strftime("%d-%m-%Y %H:%M:%S UTC%z")]
  return df

data = get_data()
data.to_csv('output.csv', index=False)