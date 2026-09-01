import requests
import json 

BASE_URL = "https://fantasy.premierleague.com/api"

def fetch(endpoint):
    url = f"{BASE_URL}/{endpoint}"         # so we donnt have to repeadetly write url+endpoint

    response = requests.get(url, timeout =10)      # timeout of 1- seconds 
    response.raise_for_status()      #instead of silently continuing , python will raise exception

    return response.json()         #fpl api will respons with JSON . converts HTTP response into python object

