import network
from time import sleep

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)

async def connect(ssid, password):
    sta_if.connect(ssid, password)
    max_tries=12
    tries=0
    while True:
        if sta_if.isconnected():
            return True
        tries = tries + 1
        if (tries >= max_tries):
            return False
        sleep(1)