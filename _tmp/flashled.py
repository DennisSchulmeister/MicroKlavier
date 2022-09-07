import pyb, time

@micropython.viper
def execute():
    led = pyb.LED(4)

    while True:
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)
