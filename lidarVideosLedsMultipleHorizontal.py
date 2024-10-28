import serial
import re
import pygame
import cv2
import time
import threading
import board
import neopixel

# Configurar puerto serie
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
print("Conectado al puerto serie. Leyendo datos...")

# Inicializar Pygame
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

# Lista de videos por zonas (1 a 4)
video_files = ["1.mp4", "2.mp4", "3.mp4", "4.mp4"]  # Asegúrate de que estos archivos existan
videos = [cv2.VideoCapture(file) for file in video_files]

# Video por defecto
default_video = cv2.VideoCapture("default.mp4")

# Variables de control
current_video = default_video
video_en_progreso = False

# Configuración de la tira LED
LED_PIN = board.D21  # Pin GPIO que usas
NUM_LEDS = 509       # Número de LEDs en la tira
BRIGHTNESS = 1       # Brillo de los LEDs

# Límites de las secciones
lim0 = 0
lim1 = 128
lim2 = 256
lim3 = 384
lim4 = 509

# Colores por zonas
colores_zonas = [(255, 0, 0),  # Zona 1: Rojo
                 (0, 255, 0),  # Zona 2: Verde
                 (0, 0, 255),  # Zona 3: Azul
                 (255, 255, 0)]  # Zona 4: Amarillo

# Color por defecto (por ejemplo, blanco suave)
color_por_defecto = (0, 255, 255)

strip = neopixel.NeoPixel(LED_PIN, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)

# Variable para controlar la animación de LEDs
stop_animation = threading.Event()

def turn_off_all_leds():
    """Apagar todos los LEDs."""
    strip.fill((0, 0, 0))
    strip.show()

def turn_on_section(r, g, b, section):
    """Encender la sección correspondiente."""
    start = 0
    end = 0

    if section == 1:
        start, end = lim0, lim1
    elif section == 2:
        start, end = lim1, lim2
    elif section == 3:
        start, end = lim2, lim3
    elif section == 4:
        start, end = lim3, lim4
    else:
        print("Sección no válida. Debe ser un número del 1 al 4.")
        return

    # Encender solo la sección especificada
    for i in range(start, end):
        strip[i] = (r, g, b)
    strip.show()

def blink_color(r, g, b, duration=10, section=2):
    """Función para parpadear un color específico en una sección durante un tiempo determinado."""
    end_time = time.time() + duration
    while time.time() < end_time:
        if stop_animation.is_set():
            return  # Salir de la animación si se solicita detenerla

        turn_on_section(r, g, b, section)  # Encender la sección
        time.sleep(0.5)  # Encendido por 0.5 segundos

        if stop_animation.is_set():
            return  # Salir de la animación si se solicita detenerla

        turn_off_all_leds()  # Apagar los LEDs
        time.sleep(0.5)  # Apagado por 0.5 segundos

    # Restaurar el color por defecto al finalizar la animación
    restore_default_led_color()

def restore_default_led_color():
    """Restaurar el color por defecto de todos los LEDs."""
    strip.fill(color_por_defecto)
    strip.show()

# Función para reproducir video
def play_video(video, speed=1.0):  # Añadir un parámetro de velocidad
    fps = 30  # Establecer FPS fijo (ajusta este valor según tus necesidades)
    
    ret, frame = video.read()
    if not ret:
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reiniciar el video
        return False
    
    # Cambiar resolución del video a 1920x1080
    frame = cv2.resize(frame, (1920, 1080))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pygame_frame = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")

    screen.blit(pygame_frame, (0, 0))
    pygame.display.flip()

    # Ajustar tiempo de espera entre frames para asegurar la velocidad correcta
    time.sleep((1 / fps) / speed)  # Modificar la velocidad aquí
    return True

# Función para obtener datos del sensor serial
def obtener_datos_sensor():
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').rstrip()
        print(f"Datos recibidos: {data}")

        # Detectar la zona y la acción (ENTER/EXIT)
        match = re.search(r'ZONE(\d+)=([A-Z]+)', data)
        if match:
            zona_numerica = int(match.group(1))
            action = match.group(2)  # ENTER o EXIT
            return zona_numerica, action
    return None, None

# Bucle principal
running = True
current_thread = None  # Almacenar el hilo actual de la animación
restore_default_led_color()  # Encender los LEDs con el color por defecto al inicio

while running:
    # Obtener datos del sensor
    zona_numerica, action = obtener_datos_sensor()

    # Si se detecta 'ENTER' en una zona válida (1-4), reproducir el video correspondiente y activar LEDs
    if action == "ENTER" and zona_numerica in range(1, 5):
        # Detener la animación de LEDs anterior si existe
        if current_thread is not None and current_thread.is_alive():
            stop_animation.set()  # Indicar que se debe detener la animación
            current_thread.join()  # Esperar a que el hilo termine

        stop_animation.clear()  # Reiniciar la señal para la nueva animación
        turn_off_all_leds()  # Apagar todos los LEDs antes de la nueva animación

        # Cambiar video
        current_video = videos[zona_numerica - 1]
        current_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        video_en_progreso = True
        print(f"Reproduciendo video {zona_numerica}.")

        # Obtener el color para la zona actual
        color = colores_zonas[zona_numerica - 1]
        # Iniciar la nueva animación de LEDs en un hilo separado
        current_thread = threading.Thread(target=blink_color, args=(color[0], color[1], color[2], 10, zona_numerica))
        current_thread.start()

    elif action == "EXIT":
        # Ignorar EXIT según tus indicaciones
        print(f"Ignorando EXIT de zona {zona_numerica}.")

    # Reproducir video actual si está en progreso
    if video_en_progreso:
        if not play_video(current_video):  # Si el video ha terminado
            video_en_progreso = False
            current_video = default_video
            current_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            print("Video terminado. Reproduciendo video por defecto.")
            # Reproducir el video por defecto a velocidad 2.0
            play_video(current_video, speed=2)  # Cambiar la velocidad aquí

    # Si no hay video en progreso, reproducir el video por defecto
    if not video_en_progreso:
        play_video(current_video, speed=2)  # Cambiar la velocidad aquí

    # Capturar eventos de teclado (salida con 'ESC' o 'q')
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:  # Salir con 'q'
                running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        running = False

# Limpiar antes de salir
if current_thread is not None and current_thread.is_alive():
    stop_animation.set()  # Detener cualquier animación en progreso
    current_thread.join()

# Liberar recursos
for video in videos:
    if video:
        video.release()
default_video.release()
cv2.destroyAllWindows()
pygame.quit()
ser.close()
