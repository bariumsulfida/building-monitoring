from bh1750 import BH1750  # Import kelas BH1750
from sht20 import SHT20  # Import kelas SHT20
from mhz19 import MHZ19  # Import kelas MH-Z19
from arduino import ModbusSensor  # Import kelas ModbusSensor
from pzem import PZEM004T  # Import kelas PZEM004T
from gas import GAS
import time
import random
import requests
import datetime

API_URL = "192.168.137.19"

def send_data(data):
    try:
        response = requests.post(API_URL, json=data)
        print(f"{datetime.now().isoformat()} - Sent data | Status: {response.status_code} | Response: {response.text}")
    except Exception as e:
        print(f"Error sending data: {str(e)}")

# Main program
if __name__ == "__main__":  
    try:
        bh1750 = BH1750()
        sht20 = SHT20()
        mhz19_sensor = MHZ19()  # Objek untuk sensor CO2 MH-Z19
        #mpu6050 = MPU6050()
        modbus_sensor = ModbusSensor()  # Inisialisasi sensor Modbus dengan port yang sudah diatur di kelas
        pzem_sensor = PZEM004T()  # Inisialisasi sensor PZEM004T
        gas = GAS()

        while True:
            lux = bh1750.read_lux()
            temp = sht20.read_temperature()
            humidity = sht20.read_humidity
            co2 = mhz19_sensor.read_co2()
            voltage, current, power = pzem_sensor.read_data()
            noise = modbus_sensor.read_register_data(0)
            deteksi_gas = gas.is_high()

            data = {
                "temp": temp,
                "humidity": humidity,
                "illuminance": lux,
                "co2": co2,
                "noise": noise,  
                "current": current,
                "voltage": voltage,
                "gas_detection": deteksi_gas,
                "people": True,
                "earthquake": False
            }
            
            send_data(data)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nProgram dihentikan.")

    finally:
        bh1750.close()
        sht20.close()
        mhz19_sensor.cleanup()  # Membersihkan konfigurasi GPIO dan sensor CO2 MH-Z19
        modbus_sensor.close()  # Menutup koneksi serial Modbus saat program dihentikan
        pzem_sensor.close()  # Menutup koneksi PZEM004T
