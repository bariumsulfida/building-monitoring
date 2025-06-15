import minimalmodbus
import serial
import time
from datetime import datetime

class PZEM004T:
    def __init__(self, port='/dev/ttyUSB1', device_address=0x01):
        """Inisialisasi koneksi dengan sensor PZEM-004T."""
        self.port = port
        self.device_address = device_address
        self.instrument = minimalmodbus.Instrument(self.port, self.device_address)
        self.instrument.serial.baudrate = 9600
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = serial.PARITY_NONE
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 1

    def read_data(self):
        """Membaca data dari sensor PZEM-004T dan menampilkan hasilnya."""
        try:
            # Read measurement data
            voltage = self.instrument.read_register(0x0000, number_of_decimals=1, functioncode=4)
            currentlow = self.instrument.read_register(0x0001, functioncode=4)
            currenthigh = self.instrument.read_register(0x0002, functioncode=4)
            current = (currenthigh << 16) + currentlow
            power_low = self.instrument.read_register(0x0003, functioncode=4)
            power_high = self.instrument.read_register(0x0004, functioncode=4)
            power = (power_high << 16) + power_low

            # Menampilkan data
            # print(f"Voltage: {voltage} V")
            # print(f"Current: {current * 0.001} A")
            # print(f"Power: {power * 0.1} W")

            # Return the data
            return voltage, current * 0.001, power * 0.1
        except minimalmodbus.IllegalRequestError as e:
            print(f"Error: {e}")
            return None, None, None

    def close(self):
        """Menutup koneksi serial ke perangkat."""
        self.instrument.serial.close()
        print("Koneksi ke perangkat ditutup.")

