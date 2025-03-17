# Programa para medir la intensidad de señal WiFi (RSSI)
# Universidad Militar Nueva Granada - Ingeniería en Telecomunicaciones
# jose.rugeles@unimilitar.edu.co

import network
import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# Configuración OLED
WIDTH = 128
HEIGHT = 32
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=200000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

# Configuración WiFi
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
ssid = "iPhone de Jose D"
password = "jrugeles"

# Conexión a la red WiFi
wifi.connect(ssid, password)
while not wifi.isconnected():
    time.sleep(1)

print("Conexión establecida!")
print("Dirección IP:", wifi.ifconfig()[0])

# Bucle principal
while True:
    rssi_values = []
    
    # Toma 10 muestras de RSSI
    for _ in range(10):
        rssi = wifi.status('rssi')
        rssi_values.append(rssi)
        time.sleep(0.2)

    # Calcula el promedio
    rssi_average = sum(rssi_values) / len(rssi_values)
    print("Promedio de RSSI:", rssi_average, "dBm")
    
    # Visualización OLED
    oled.fill(0)
    oled.invert(True)
    oled.text("RSSI:", 2, 6)
    oled.text(str(round(rssi_average, 2)) + " dBm", 10, 20)
    oled.show()
    
    time.sleep(2)
