import serial
import requests

# Ajusta el puerto según tu PC
ser = serial.Serial("COM6", 115200)

while True:
    line = ser.readline().decode().strip()

    try:
        mac, rssi = line.split(",")

        data = {
            "mac": mac,
            "rssi": int(rssi)
        }

        response = requests.post(
            "http://172.16.99.158:8000/data",
            json=data
        )

        print("Enviado:", data)

    except Exception as e:
        print("Error:", e)