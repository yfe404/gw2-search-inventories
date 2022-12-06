import os
import json
import requests

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Form

from pydantic import BaseModel

from typing import Union, List
from fastapi import FastAPI

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class Item(BaseModel):
    label: str
    value: str
    id: str

class Apikey(BaseModel):
    key: str
    name: str

class Apikeys(BaseModel):
    apikeys: List[Apikey]

class SearchRequest(BaseModel):
    selected_item: Item
    apikeys: Apikeys
    

@app.get("/")
def main():
    return templates.TemplateResponse("index.html", {"request": {}})


@app.post("/refresh")
def refresh(apikeys: Apikeys):

    
    for idx, api_key in enumerate(apikeys.apikeys):
        with open(f"./cache/{api_key.key}.json", "w") as f:
            BASE_URL = "https://api.guildwars2.com/v2"
            SUFFIX = f"?access_token={api_key.key}"
            account = {}
            
            res = requests.get(f"{BASE_URL}/account{SUFFIX}")
            print(res.json())
            print(res.status_code)
            account_name = res.json()["name"]
            account["name"] = account_name
    
            print("Downloading bank content")
            res = requests.get(f"{BASE_URL}/account/bank{SUFFIX}")
            bank = [x for x in res.json() if x is not None]
            account["bank"] = bank

            print("Downloading shared inventory content")
            res = requests.get(f"{BASE_URL}/account/inventory{SUFFIX}")
            shared = [x for x in res.json() if x is not None]
            account["shared"] = shared

            print("Downloading material storage content")
            res = requests.get(f"{BASE_URL}/account/materials{SUFFIX}")
            materials = [x for x in res.json() if x is not None]
            account["materials"] = materials

            print("Downloading character inventories content")
            res = requests.get(f"{BASE_URL}/characters{SUFFIX}")
            characters = res.json()

            inventories = []
            for character in characters:
                res = requests.get(f"{BASE_URL}/characters/{character}/inventory{SUFFIX}")
                inventories.append(res.json())
                account["inventories"] = inventories
                account["characters"] = characters

            f.write(json.dumps(account))
            
    return templates.TemplateResponse("settings.html", {"request": {}})


    


@app.get("/settings")
def main():
    return templates.TemplateResponse("settings.html", {"request": {}})


@app.post("/search")
async def search(request: SearchRequest):
#    print (request)

    searched_item = int(request.selected_item.id)
    total_owned = 0

    accounts = []
    
    
    for apikey in request.apikeys.apikeys:
        print(apikey.key)

        if os.path.exists(os.path.join("cache", f"{apikey.key}.json")):
            with open(os.path.join("cache", f"{apikey.key}.json"), "r") as f:
                cache_content = json.loads(f.read())

            account_details = {"name": cache_content["name"]}
            

#            print(f"==== {accounts[idx]['name']} ====")

            account_details["shared_inventory"] = 0 
            for item in cache_content['shared']:
                if item["id"] == searched_item:
                    account_details["shared_inventory"] += item['count']
                    total_owned += item['count']

            account_details["bank"] = 0
            for item in cache_content['bank']:
                if item["id"] == searched_item:
                    account_details["bank"] += item['count']
                    total_owned += item['count']

            account_details["material_storage"] = 0
            for item in cache_content['materials']:
                if item["id"] == searched_item:
                    account_details["material_storage"] += item['count']
                    total_owned += item['count']


            print("+++++++++++++++++++++++++++++++++++++++++++++++++")
            account_details["inventories"] = {}
            account_details["inventories"]["characters"] = []
            total_all_char = 0
            for i in range(len(cache_content['characters'])):
                total_qty = 0
                for j, bag in enumerate(cache_content['inventories'][i]["bags"]):
                    if bag is not None:
                        for item in bag["inventory"]:
                            if item is not None:
                                if item["id"] == searched_item:
                                    total_qty += item['count']
                print(f"\t{cache_content['characters'][i]} carries {total_qty} Vicious claws")
                total_owned += total_qty
                total_all_char += total_qty


                account_details["inventories"]["characters"].append(
                    {
                        "name": cache_content['characters'][i],
                        "qty": total_qty
                    }
                )
        
            account_details["inventories"]["qty"] = total_all_char
        accounts.append(account_details)
        
    response = {
        "total_owned": total_owned,
        "accounts": accounts
    }

    return response




@app.get("/autocomplete")
def autocomplete(term: str):


    #headers = 

    #-H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0' -H 'Accept: text/plain, */*; q=0.01' -H 'Accept-Language: fr,en-US;q=0.7,en;q=0.3' -H 'Accept-Encoding: gzip, deflate, br' -H 'X-Requested-With: XMLHttpRequest' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Referer: https://db.gw2.fr/' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-origin' -H 'Sec-GPC: 1' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache'


    
    res = requests.get(f"https://db.gw2.fr/autocomplete?query={term}")

    from pprint import pprint
    pprint(res.json())

    response = []
    for item in res.json()["suggestions"]:
        response.append({
            "label": item["value"],
            "value": item["value"],
            "id": item["data"]
        })
    
    return response
