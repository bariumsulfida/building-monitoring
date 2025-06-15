import RPi.GPIO as GPIO
import time

class GAS:
    def __init__(self, pin1=11, pin2=9):
        """
        Inisialisasi GPIOStateChecker dengan dua pin GPIO
        
        :param pin1: Nomor pin GPIO pertama
        :param pin2: Nomor pin GPIO kedua
        """
        self.TGS_PIN = pin1
        self.MQ6_PIN = pin2
        
        # Setup mode GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Set pin sebagai input dengan pull-up resistor internal
        GPIO.setup(self.TGS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.MQ6_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
    def get_states(self):
        """
        Mendapatkan state dari kedua pin
        
        :return: Dictionary berisi state dari kedua pin
        """
        state_TGS = GPIO.input(self.TGS_PIN)
        state_MQ6 = GPIO.input(self.MQ6_PIN)
        
        return state_TGS, state_MQ6
    
    def is_high(self, pin):
        return GPIO.input(self.TGS_PIN) == GPIO.HIGH or GPIO.input(self.MQ6_PIN) == GPIO.HIGH

        
    def cleanup(self):
        """
        Membersihkan setup GPIO
        """
        GPIO.cleanup()

