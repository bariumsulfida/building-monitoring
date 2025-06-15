import time
import RPi.GPIO as GPIO

class MHZ19:
    def __init__(self, pwm_pin=18, servo_pin=17, pin11=11, pin9=9):
        """Inisialisasi sensor MH-Z19 (PWM), pin GPIO untuk servo, dan pin kontrol eksternal."""
        self.pwm_pin = pwm_pin
        self.servo_pin = servo_pin
        self.TGS_PIN = pin11
        self.MQ6_PIN = pin9

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pwm_pin, GPIO.IN)
        GPIO.setup(self.servo_pin, GPIO.OUT)
        GPIO.setup(self.TGS_PIN, GPIO.IN)
        GPIO.setup(self.MQ6_PIN, GPIO.IN)

        self.pwm = GPIO.PWM(self.servo_pin, 50)  # 50Hz
        self.pwm.start(7)  # Mulai PWM dengan duty cycle 7% (posisi 0 derajat)

    # Fungsi untuk membaca data CO2 dari sensor MH-Z19 via PWM
    def read_co2(self, duration=1.004):
        """Membaca data CO2 dari sensor MH-Z19 melalui sinyal PWM"""
        start_time = time.time()
        high_time = 0
        low_time = 0

        while (time.time() - start_time) < duration:
            if GPIO.input(self.pwm_pin) == GPIO.LOW:
                low_start = time.time()
                while GPIO.input(self.pwm_pin) == GPIO.LOW:
                    pass
                low_time += time.time() - low_start
            if GPIO.input(self.pwm_pin) == GPIO.HIGH:
                high_start = time.time()
                while GPIO.input(self.pwm_pin) == GPIO.HIGH:
                    pass
                high_time += time.time() - high_start

        # Rumus konversi sesuai datasheet MH-Z19 PWM
        try:
            co2_ppm = 2000 * ((high_time - 0.002) / (high_time + low_time - 0.004))
            return round(co2_ppm)
        except ZeroDivisionError:
            return None

    # Fungsi untuk mengendalikan servo berdasarkan nilai CO2 menggunakan PWM
    def control_servo(self, co2_value):
        if co2_value > 3000 or GPIO.input(self.TGS_PIN) == GPIO.HIGH or GPIO.input(self.MQ6_PIN) == GPIO.HIGH:
            # Jika CO2 > 3000 ppm atau pin 5/6 HIGH, servo bergerak ke 120 derajat
            print("CO2 concentration above 3000 ppm! Moving servo to 120 degrees...")
            self.pwm.ChangeDutyCycle(7)  # Sesuaikan dengan penyesuaian untuk 120 derajat
        else:
            print("CO2 concentration normal. Moving servo to 0 degrees...")
            self.pwm.ChangeDutyCycle(2)  # Sesuaikan dengan penyesuaian untuk 0 derajat

    def stop_pwm(self):
        """Menghentikan PWM untuk servo."""
        self.pwm.stop()

    def cleanup(self):
        """Membersihkan konfigurasi GPIO saat program dihentikan."""
        GPIO.cleanup()

    def print_data(self):
        """Menampilkan data CO2 dan menggerakkan servo jika diperlukan."""
        co2_value = self.read_co2()
        pin5_high = GPIO.input(self.TGS_PIN) == GPIO.HIGH
        pin6_high = GPIO.input(self.MQ6_PIN) == GPIO.HIGH

        if co2_value is not None:
            print(f"CO2 Concentration: {co2_value} ppm")
            # Servo bergerak jika CO2 tinggi atau pin 5/6 HIGH
            if co2_value > 3000 or pin5_high or pin6_high:
                print("Trigger: CO2 tinggi atau pin 5/6 HIGH")
                self.pwm.ChangeDutyCycle(12)  # 120 derajat
            else:
                self.pwm.ChangeDutyCycle(2)   # 0 derajat
        else:
            print("Gagal membaca data dari sensor MH-Z19 (PWM).")
