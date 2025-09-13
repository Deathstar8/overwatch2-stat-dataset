import pandas as pd
import json
import requests
import itertools
from bs4 import BeautifulSoup
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8,application/json",
    "Accept-Language": "en-US,en;q=0.5"
}

site_html = requests.get('https://overwatch.blizzard.com/en-us/rates/', headers=headers).text
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

#Fetch titles for game modes and put them in a dictionary
for i in param:
  if i.parent.has_attr('data-label') and i.parent['data-label'] == "rq":
    rq_dict.update({i['value'] : i['data-title']})

param_combos = list(itertools.product(input_values, rq_values, tier_values, region_values, map_values))

def get_data(param_combos, warning=False):
  output = pd.DataFrame()
  timestamp = datetime.now().astimezone().strftime("%d-%m-%Y %H:%M:%S UTC%z")

  for i in param_combos:

    params = {"input" : i[0], "map" : i[4], "region" : i[3], "role" : "All", "rq" : i[1], "tier" : i[2]}

    #Hardcoded way to stop requesting QP data that will be immediately be discarded
    #I don't like this, but I can't think of a way to automatically detect if a game mode utilizes the tier parameter right now
    if i[1] == "Quick Play - Role Queue" and i[2] != "All":
      continue

    data_request = requests.get("https://overwatch.blizzard.com/en-us/rates/data/", params=params, headers=headers)
    if data_request.status_code != 200 and data_request.status_code == 404:
      print("Error! Data not found!")
      break
    elif data_request.status_code != 200:
      print("Warning, encountered unexpected status code: " + str(data_request.status_code))
      print("Broke on inputs: " + str(params))
      break

    data = json.loads(data_request.text)

    #Check if loaded data params matches input params
    #If they don't match, it probably means the input params were invalid (like fetching winrates based on competitive rank, but selecting Quick Play)
    if data['selected'] != params:
      if warning == True:
        print("Warning: Fetched data has different parameters than input parameters. Fetched data is most likely not reflective of input parameters.")
        print("Input parameters: " + str(params))
        print("Recieved (selected by website) parameters: " + str(data['selected']))
      continue

    df = pd.DataFrame(pd.json_normalize(data["rates"])).drop(columns=["id", "hero.portrait", "hero.name", "hero.color", "hero.roleIcon"]).rename(columns={"cells.name" : "Hero", "cells.pickrate" : "Pick rate", "cells.winrate" : "Win rate", "hero.role" : "Role"})
    df[["Input", "Game Mode", "Tier", "Map", "Region", "Timestamp"]] = [data['selected']["input"], rq_dict[data['selected']["rq"]], data['selected']["tier"], data['selected']["map"], data['selected']["region"], timestamp]
    output = pd.concat([output, df], ignore_index=True)
  return output

data = get_data(param_combos)
data.to_csv('output.csv', index=False)