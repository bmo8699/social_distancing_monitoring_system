import asyncio
import websockets
import seeed_dht

async def main(websocket):
    print("----")
    sensor = seeed_dht.DHT("11", 12)
    while True:
        humi, temp = sensor.read()
        print("temp",temp,"humi", humi)
        if not humi is None:
            await websocket.send(str(humi) + ' ' + str(temp))
    

async def run_server():
    async with websockets.serve(main, "0.0.0.0", 8081):
        await asyncio.Future()
        

asyncio.run(run_server())