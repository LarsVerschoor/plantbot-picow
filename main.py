# In this file:
# The pico w advertises as a Bluetooth Low Energy (BLE) Peripheral.
# The pico w listens for a WIFI credentials write from the BLE Central.
# The pico w connects to the WIFI network.
# The pico w connects to the api.plantbot.nl server via a WebSocket protocol.

import sys
from micropython import const
import asyncio
import aioble
import bluetooth
import random
from wifi import connect
from plantbot_server import connect_websocket

# Bluetooth UUID's for peripheral services and characteristics
WIFI_CREDENTIALS_SERVICE_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
WIFI_SSID_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")
WIFI_PASSWORD_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef2")
WIFI_NOTIFICATIONS_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef3")

# BLE peripheral advertising interval
_ADV_INTERVAL_MS = 500

wifi_ssid = None
wifi_password = None

# Register GATT server
credentials_service = aioble.Service(WIFI_CREDENTIALS_SERVICE_UUID)

# Create characteristics and add to the service
ssid_characteristic = aioble.Characteristic(credentials_service, WIFI_SSID_CHAR_UUID, read=True, write=True, capture=True)
password_characteristic = aioble.Characteristic(credentials_service, WIFI_PASSWORD_CHAR_UUID, read=True, write=True, capture=True)
notifications_characteristic = aioble.Characteristic(credentials_service, WIFI_NOTIFICATIONS_CHAR_UUID, notify=True)
aioble.register_services(credentials_service)

# Await credentials write from the central
# Decode the raw write bytes to an utf-8 string
# Try to connect, notify the central of the result
async def handle_credentials_write(connection):
    global wifi_ssid, wifi_password

    conn, encoded_ssid = await ssid_characteristic.written()
    decoded_ssid = encoded_ssid.decode('utf-8')
    wifi_ssid = decoded_ssid

    conn, encoded_password = await password_characteristic.written()
    decoded_password = encoded_password.decode('utf-8')
    wifi_password = decoded_password
    
    notifications_characteristic.notify(connection, b'connecting:starting')
    
    connected = await connect(wifi_ssid, wifi_password)
    message = b'connecting:success' if connected == True else b'connecting:failed'
    notifications_characteristic.notify(connection, message)
    
    if (connected == True):
        connect_websocket()


# Wait for a connection. Not advertising when a BLE Central is connected.
async def peripheral_task():
    while True:
        async with await aioble.advertise(_ADV_INTERVAL_MS, name="PlantBot", services=[WIFI_CREDENTIALS_SERVICE_UUID],) as connection:
            print("Connection from", connection.device)
            await handle_credentials_write(connection)
            await connection.disconnected(timeout_ms=None)

async def main():
    await peripheral_task()

asyncio.run(main())