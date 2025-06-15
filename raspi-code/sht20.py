import smbus
import time

class SHT20:
    def __init__(self, bus_number=1, address=0x40):
        """Inisialisasi sensor SHT20."""
        self.bus = smbus.SMBus(bus_number)  # Inisialisasi I2C bus
        self.address = address

    def read_temperature(self):
        """Membaca suhu dari sensor SHT20."""
        try:
            self.bus.write_byte(self.address, 0xE3)  # Perintah untuk baca suhu
            time.sleep(0.1)
            data = self.bus.read_i2c_block_data(self.address, 0xE3, 2)
            temp_raw = (data[0] << 8) | data[1]
            temperature = -46.85 + 175.72 * (temp_raw / 65536.0)
            return round(temperature, 2)
        except Exception as e:
            return f"Error membaca suhu: {e}"

    def read_humidity(self):
        """Membaca kelembapan dari sensor SHT20."""
        try:
            self.bus.write_byte(self.address, 0xE5)  # Perintah untuk baca kelembapan
            time.sleep(0.1)
            data = self.bus.read_i2c_block_data(self.address, 0xE5, 2)
            hum_raw = (data[0] << 8) | data[1]
            humidity = -6.0 + 125.0 * (hum_raw / 65536.0)
            return round(humidity, 2)
        except Exception as e:
            return f"Error membaca kelembapan: {e}"

    def print_data(self):
        """Membaca dan mencetak suhu serta kelembapan."""
        temperature = self.read_temperature()
        humidity = self.read_humidity()

        timestamp = time.strftime("%H:%M:%S")  # Timestamp jam:menit:detik
        print(f"{timestamp}")
        if isinstance(temperature, float) and isinstance(humidity, float):
            print(f"SHT20 | Suhu: {temperature}°C | Kelembaban: {humidity}%")
        else:
            print("SHT20 | Data tidak terbaca")

    def close(self):
        """Menutup koneksi I2C bus."""
        self.bus.close()
