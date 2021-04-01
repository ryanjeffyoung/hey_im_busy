from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from app.api.server import setup, checkAvailable, freeWhen, busyWhen 

app = FastAPI() #create FastAPI instance
g_api = setup() # establish google calendar API service

@app.get("/")
async def root():
    resp = {"Message": "Hello World"}
    json_response = jsonable_encoder(resp)
    return json_response
@app.get("/status")
async def status():
    available = checkAvailable(g_api)

    if available:
        return {"status" : "Free",
                "next_available" : None,
                "next_busy" : busyWhen(g_api)}
    else:
        return {"status" : "Busy",
                "next_available" : freeWhen(g_api),
                "next_busy" : None}


