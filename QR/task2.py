import sys
import time
from grove.gpio import GPIO
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from grove.display.jhd1802 import JHD1802
import websockets
import asyncio
import multiprocessing

async def main(websocket):
    print("something")
    with open('data.txt') as f:
        dataList = f.read().splitlines()
        
    population = 0
    current_population = population
    current_scanner = None
    triggered_flag = None
    triggered_time = None
    decrease_flag = False
    
    capture = cv2.VideoCapture(0)
    capture.set(3, 640) 
    capture.set(4, 480)
    print(dataList)
    lcd = JHD1802()
    prompt_time = 0
    
    clear = False

    manager = multiprocessing.Manager()
    lst = manager.list()
    lst.append(None)
    
    population_increase_flag = False

    authenticated_flag = False
    unauthenticated_flag = False 

    scanning = False
    last_entered_time = 0
    while True:
        enter_file = open("enter.txt","r")
        print(population)
        if enter_file.read():
            last_entered_time = time.time()
            if not scanning and not authenticated_flag and population < 5:
                lcd.clear()
                lcd.setCursor(0, 0)
                lcd.write("Please scan...")
            scanning = False
            enter_file.close()
            if population < 5:
                success, img = capture.read()
                if img is None:
                    capture = cv2.VideoCapture(0)
                else:    
                    for barcode in decode(img):
                        data = barcode.data.decode('utf-8')
                        if data in dataList:
                            result  = 'Authorized - Welcome ' + data + '!'
                            authenticated_flag = True
                            color = (52,235,91)
                            lcd.setCursor(0, 0)
                            lcd.clear()
                            lcd.write("Welcome")
                            lcd.setCursor(1,0)
                            lcd.write(data)
                            scanning = True
                            if not population_increase_flag:
                                population += 1
                                population_increase_flag = True
                                authenticated_file = open("authenticated.txt", "w")
                                authenticated_file.write("1")
                                authenticated_file.close()
                            clear = False
                        else:
                            result = 'Unauthorized - Cannot enter ' + data + '!'
                            color = (237,22,7)
                            lcd.setCursor(0, 0)
                            lcd.clear()
                            lcd.write("Unauthorized")
                            clear = False
                            scanning = True
                            unauthenticated_flag = True
                        points1= np.array([barcode.polygon], np.int32)
                        points1 = points1.reshape((-1,1,2))
                        cv2.polylines(img,[points1], True, color, 5)
                        points2 = barcode.rect
                        cv2.putText(img, result, (points2[0], points2[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 2)
                    cv2.imshow('Result',img)
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 65]
                    lst[0] = cv2.imencode('.jpg', img, encode_param)[1]
                    await websocket.send(lst[0].tobytes())
                    cv2.waitKey(1)
            else:
                if not authenticated_flag:
                    lcd.setCursor(0, 0)
                    lcd.write("Room full")
                    clear = False
        else:
            if not clear:
                lcd.clear()
                clear = True
            enter_file.close()
            population_increase_flag = False
            #cv2.destroyAllWindows()
            capture.release()
            leave_file = open('leave.txt', 'r')
            if leave_file.read():
                leave_file.close()
                if (population > 0):  
                    population = population - 1
                print("================================")
                leave_file = open('leave.txt', 'w')
                leave_file.write("")
                leave_file.close()
            if time.time() - last_entered_time < 3 and not authenticated_flag and population < 5:
                lcd.setCursor(0, 0)
                lcd.write("Scan time out")
                lcd.setCursor(1, 0)
                lcd.write("Please leave")
            else:
                clear = False
            if authenticated_flag and time.time() - last_entered_time > 10:
                authenticated_flag = False
                authenticated_file = open("authenticated.txt", "w")
                authenticated_file.write("")
                authenticated_file.close()
            unauthenticated_flag = False
            time.sleep(0.1)

        await websocket.send(str(population))

async def run_server():
    async with websockets.serve(main, "0.0.0.0", 5000):
        await asyncio.Future()


if __name__ == '__main__':
    manager = multiprocessing.Manager()
    lst = manager.list()
    lst.append(None)
    asyncio.run(run_server())

