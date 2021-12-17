import RPi.GPIO as GPIO # On Raspberry Pi
# import GPIO  # On Other Platforms
import time

# Connect PUL to pin 11, DIR to pin 13, ENB to pin 15.
pul_pin = 11
dir_pin = 13
enb_pin = 15
pulse_per_rev = 400


def setup_GPIO_pins():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(pul_pin, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(dir_pin, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(enb_pin, GPIO.OUT, initial=GPIO.LOW)


def cleanup_pins():
    GPIO.cleanup()


def disable_motor():
    setup_GPIO_pins()
    GPIO.output(enb_pin, GPIO.HIGH)


def enable_motor():
    GPIO.output(enb_pin, GPIO.LOW)


def set_reverse():
    GPIO.output(dir_pin, GPIO.HIGH)


def cancel_reverse():
    GPIO.output(dir_pin, GPIO.LOW)


def start_motor(rev_per_second, run_time, reverse):
    enable_motor()
    if reverse:
        set_reverse()
    else:
        cancel_reverse()
    pulse_per_second = rev_per_second * pulse_per_rev
    pulse_time_interval = float(1) / float(pulse_per_second)
    pulse_times = int(run_time / pulse_time_interval) * 5
    time_counter = 0
    print(pulse_time_interval / 2)
    while True:
        time_counter += 1
        GPIO.output(pul_pin, 0)
        time.sleep(pulse_time_interval / 10)  # Don't know, there's a 5x scaling.
        GPIO.output(pul_pin, 1)
        time.sleep(pulse_time_interval / 10)
        if time_counter >= pulse_times:
            break
    if reverse:
        cancel_reverse()
    disable_motor()
