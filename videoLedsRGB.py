import RPi.GPIO as GPIO
import time
import cv2
import numpy as np

# Configuración de los pines GPIO
RED_PIN = 24
GREEN_PIN = 22
BLUE_PIN = 17

# Configuración de GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

# Crear PWM para cada canal de color con frecuencia de 100 Hz
red_pwm = GPIO.PWM(RED_PIN, 100)  
green_pwm = GPIO.PWM(GREEN_PIN, 100)
blue_pwm = GPIO.PWM(BLUE_PIN, 100)

# Iniciar PWM en 0% de duty cycle
red_pwm.start(0)
green_pwm.start(0)
blue_pwm.start(0)

# Clase Video para administrar las propiedades de cada video
class Video:
    def __init__(self, id, rgb, video_file, num_repeticiones):
        self.id = id
        self.rgb = rgb  # Color RGB para el LED
        self.video_file = video_file  # Ruta del archivo de video
        self.num_repeticiones = num_repeticiones  # Número de repeticiones

# Función para escalar valores RGB de 0-255 a 0-100 para PWM
def scale_rgb(value):
    return (value / 255) * 100

# Función para configurar el color del LED usando PWM
def set_color(rgb):
    # Apagar el LED rápidamente
    red_pwm.ChangeDutyCycle(0)
    green_pwm.ChangeDutyCycle(0)
    blue_pwm.ChangeDutyCycle(0)
    time.sleep(0.05)  # Pausa breve para asegurarse de que el LED esté apagado

    # Establecer el nuevo color
    red_pwm.ChangeDutyCycle(scale_rgb(rgb[0]))
    green_pwm.ChangeDutyCycle(scale_rgb(rgb[1]))
    blue_pwm.ChangeDutyCycle(scale_rgb(rgb[2]))

# Crear un fondo negro en pantalla completa
def show_black_background(window_name="Reproduciendo video"):
    black_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.imshow(window_name, black_frame)
    cv2.waitKey(1)

# Función para reproducir video redimensionado a pantalla completa
def play_video(video_path, window_name="Reproduciendo video"):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error al abrir el video: {video_path}")
        return False

    # Configura la ventana a pantalla completa y oculta el cursor
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback(window_name, lambda *args: None)  # Oculta el cursor

    # Obtener las dimensiones de la pantalla
    screen_width = 1920
    screen_height = 1080  # Cambiado a 1080 para pantalla completa

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Redimensionar el frame para que abarque toda la pantalla en la parte superior
        frame_resized = cv2.resize(frame, (screen_width, screen_height // 2))  # Redimensionar a la mitad de la altura

        # Crear un fondo negro en la parte inferior
        black_frame = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)
        black_frame[0:frame_resized.shape[0], 0:frame_resized.shape[1]] = frame_resized  # Colocar el video en la parte superior

        # Mostrar el frame redimensionado
        cv2.imshow(window_name, black_frame)

        # Control de velocidad de reproducción y cierre con "q"
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return "stop"

    cap.release()
    return True

# Definición de los videos en secuencia
videos = [
    Video(1, (255, 0, 0), "video1.mp4", 1),      # RGB: Rojo
    Video(2, (255, 100, 5), "video2.mp4", 1),    # RGB: Naranja
    Video(3, (0, 255, 0), "video3.mp4", 1)   # RGB: Verde
]

try:
    # Reproducción en secuencia infinita sin cerrar la ventana
    while True:
        for video in videos:
            print(f"Reproduciendo Video ID: {video.id}, Color LED: {video.rgb}, Repeticiones: {video.num_repeticiones}")
            
            # Cambiar el color solo al inicio del video
            set_color(video.rgb)

            for _ in range(video.num_repeticiones):
                # Reproduce el video y verifica si se presionó "q" para detener el programa
                if play_video(video.video_file) == "stop":
                    raise KeyboardInterrupt  # Levanta una interrupción para salir del bucle principal

        # Muestra un fondo negro después de cada secuencia de videos para evitar ver el escritorio
        show_black_background()

finally:
    # Apagar todos los LEDs y limpiar los pines GPIO al finalizar
    set_color((0, 0, 0))
    red_pwm.stop()
    green_pwm.stop()
    blue_pwm.stop()
    GPIO.cleanup()
