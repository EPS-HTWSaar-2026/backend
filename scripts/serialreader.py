import serial
import json

ser = serial.Serial("COM6", 115200, timeout=1)

buffer = ""

print("Listening TAG ...\n")

def format_mac(hex_string):
    mac_raw = hex_string[:12] 
    mac = ":".join(mac_raw[i:i+2] for i in range(0, 12, 2))
    return mac.upper()


while True:
    data = ser.read(ser.in_waiting or 1)

    if data:
        chunk = data.decode(errors="ignore")
        buffer += chunk

        while "{" in buffer and "}" in buffer:
            start = buffer.find("{")
            end = buffer.find("}") + 1

            json_str = buffer[start:end]
            buffer = buffer[end:]

            try:
                parsed = json.loads(json_str)

                raw_mac = parsed.get("transmitterAddr")
                rssi = parsed.get("rssi")

                mac = format_mac(raw_mac)

                print("MAC :", mac)
                print("RSSI:", rssi)
                print("-" * 40)

                """
                print("FULL JSON:", parsed)
                print("=" * 60)
                """

            except json.JSONDecodeError:
                print("JSON invalid:", json_str)