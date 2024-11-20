import RPi.GPIO as GPIO
import time

# Configuración de los pines GPIO
RED_PIN = 24
GREEN_PIN = 22
BLUE_PIN = 17

# Configuración de GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

# Crear PWM en cada canal de color con una frecuencia de 100 Hz
red_pwm = GPIO.PWM(RED_PIN, 100)
green_pwm = GPIO.PWM(GREEN_PIN, 100)
blue_pwm = GPIO.PWM(BLUE_PIN, 100)

# Iniciar PWM en 0% de duty cycle
red_pwm.start(0)
green_pwm.start(0)
blue_pwm.start(0)

# Función para escalar valores RGB de 0-255 a 0-100 para PWM
def scale_255_to_100(value):
    return (value / 255) * 100

# Función para actualizar el color de la tira LED
def set_color(r, g, b):
    red_pwm.ChangeDutyCycle(scale_255_to_100(r))
    green_pwm.ChangeDutyCycle(scale_255_to_100(g))
    blue_pwm.ChangeDutyCycle(scale_255_to_100(b))

# Definición de los colores en RGB
colors = [
    {"name": "Naranja", "rgb": (255, 0, 0)},  # Naranja
    {"name": "Morado", "rgb": (0, 255, 0)},   # Morado
    {"name": "Cyan", "rgb": (255, 255, 0)}      # Cyan
]

try:
    while True:
        for color in colors:
            # Configurar el color actual
            r, g, b = color["rgb"]
            set_color(r, g, b)
            print(f"Cambiando a color {color['name']} RGB({r}, {g}, {b})")

            # Mantener el color actual durante 5 segundos
            time.sleep(5)

except KeyboardInterrupt:
    pass
finally:
    # Apagar los LEDs y limpiar los pines GPIO al finalizar
    set_color(0, 0, 0)
    red_pwm.stop()
    green_pwm.stop()
    blue_pwm.stop()
    GPIO.cleanup()
