import smbus
import time
import RPi.GPIO as GPIO

class BH1750:

    def __init__(self, bus_number=1, address=0x23, relay_pin=27):
        """Inisialisasi sensor BH1750 dan pin GPIO untuk relay."""
        self.bus = smbus.SMBus(bus_number)  # Inisialisasi I2C bus
        self.address = address
        self.relay_pin = relay_pin
        
        # Setup GPIO untuk relay
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.relay_pin, GPIO.OUT)

    def read_lux(self):
        """Membaca nilai lux dari sensor BH1750."""
        try:
            self.bus.write_byte(self.address, 0x10)  # Perintah untuk baca lux
            time.sleep(0.2)  # Delay untuk memberi waktu sensor mengumpulkan data
            data = self.bus.read_i2c_block_data(self.address, 0, 2)
            lux = (data[0] << 8) + data[1]
            lux /= 1.2  # Menghitung lux dalam satuan yang benar
            return lux
        except Exception as e:
            print(f"Error membaca sensor BH1750: {e}")
            return None

    def control_relay(self, lux_value):
        """Mengontrol relay berdasarkan nilai lux."""
        if lux_value is not None:
            if lux_value < 1000:
                GPIO.output(self.relay_pin, GPIO.LOW)  # Relay aktif (ON) untuk active low
                print("Relay ON - Lux value is less than 1000")
            else:
                GPIO.output(self.relay_pin, GPIO.HIGH)  # Relay mati (OFF) untuk active low
                print("Relay OFF - Lux value is greater than or equal to 1000")

    def print_data(self):
        """Membaca dan menampilkan data lux serta mengontrol relay."""
        lux_value = self.read_lux()
        if lux_value is not None:
            print(f"Lux Value: {lux_value:.2f} lx")
        self.control_relay(lux_value)  # Mengontrol relay berdasarkan nilai lux

    def close(self):
        """Menutup koneksi I2C bus dan membersihkan GPIO."""
        self.bus.close()
        GPIO.cleanup()

if __name__ == "__main__":
    # Inisialisasi objek BH1750
    # Sesuaikan bus_number dan relay_pin jika konfigurasi Anda berbeda
    # bus_number = 1 umumnya untuk Raspberry Pi 2/3/4, 0 untuk model lama
    # relay_pin = 27 (GPIO27) adalah contoh, pastikan sesuai dengan koneksi Anda
    light_sensor_controller = BH1750(bus_number=1, address=0x23, relay_pin=27)

    try:
        while True:
            light_sensor_controller.print_data()
            time.sleep(2)  # Tunggu 2 detik sebelum membaca lagi
    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
    finally:
        light_sensor_controller.close()
        print("GPIO dibersihkan dan koneksi I2C ditutup.")