import serial
import re
import pygame
import cv2
import time

# Configurar puerto serie
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
print("Conectado al puerto serie. Leyendo datos...")

# Inicializar Pygame
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

# Lista de videos por zonas (1 a 3)
video_files = ["1.mp4", "2.mp4", "3.mp4"]  # Asegúrate de que estos archivos existan
videos = [cv2.VideoCapture(file) for file in video_files]

# Video por defecto
default_video = cv2.VideoCapture("default.mp4")

# Variables de control
current_video = default_video
video_en_progreso = False

# Función para reproducir video
def play_video(video, speed=1.0):  # Añadir un parámetro de velocidad
    fps = 30  # Establecer FPS fijo (ajusta este valor según tus necesidades)
    
    ret, frame = video.read()
    if not ret:
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reiniciar el video
        return False
    
    # Cambiar resolución del video a 1920x1080
    frame = cv2.resize(frame, (1280, 800))
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
current_video.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Asegurarnos de que el video por defecto empiece desde el principio

while running:
    # Obtener datos del sensor
    zona_numerica, action = obtener_datos_sensor()

    # Si se detecta 'ENTER' en una zona válida (1-3), reproducir el video correspondiente
    if action == "ENTER" and zona_numerica in range(1, 4):
        # Detener la reproducción anterior si es necesario
        if video_en_progreso:
            video_en_progreso = False
            current_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            print("Video cambiado.")

        # Cambiar video
        current_video = videos[zona_numerica - 1]
        current_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        video_en_progreso = True
        print(f"Reproduciendo video {zona_numerica}.")

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
for video in videos:
    if video:
        video.release()
default_video.release()
cv2.destroyAllWindows()
pygame.quit()
ser.close()
