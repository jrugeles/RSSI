import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
import sys

# Configuración del backend para evitar problemas en algunos entornos
plt.switch_backend('TkAgg')  # Cambiar a un backend más estable si es necesario

# Definir las posiciones de los nodos fijos (en 2D)
nodos_fijos = np.array([[0, 0], [10, 0], [10, 10], [0, 10]])

# Etiquetas para los nodos
etiquetas_nodos = ['Nodo 1 (0,0)', 'Nodo 2 (10,0)', 'Nodo 3 (10,10)', 'Nodo 4 (0,10)']

# Definir el nodo móvil (inicia en el centro)
nodo_movil = np.array([5, 5])

# Historial de distancias
distancias_historicas = {f'R{i+1}': [] for i in range(4)}

# Lista para la trayectoria del nodo móvil (rastro)
trayectoria_x = []
trayectoria_y = []

# Generar señales simuladas para el acelerómetro y el giroscopio (como en el segundo código)
np.random.seed(42)
acelerometro = 0.5 * np.cumsum(np.random.randn(3, 200), axis=1)  # Más realista con cumsum
giroscopio = 0.3 * np.cumsum(np.random.randn(3, 200), axis=1)

# Colores para los ejes de los sensores (como en el segundo código)
COLORES_SENSORES = {
    'acelerometro': ['#d73027', '#fc8d59', '#fee090'],  # Colores para X, Y, Z
    'giroscopio': ['#4575b4', '#91bfdb', '#e0f3f8']
}

# Función para calcular la distancia entre dos puntos
def calcular_distancia(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# Crear la figura con GridSpec (como en el primer código)
fig = plt.figure(figsize=(12, 6))
grid = plt.GridSpec(3, 4, wspace=0.3, hspace=0.3)

# Subplot principal (izquierda) - ocupa 3 filas y 3 columnas
ax_main = fig.add_subplot(grid[:, :3])

# Subplots a la derecha (apilados verticalmente) - cada uno ocupa 1 fila y 1 columna
ax_right1 = fig.add_subplot(grid[0, 3])  # Distancias históricas
ax_right2 = fig.add_subplot(grid[1, 3])  # Acelerómetro
ax_right3 = fig.add_subplot(grid[2, 3])  # Giroscopio

# Configurar el subplot principal
ax_main.set_xlim(-1, 11)
ax_main.set_ylim(-1, 11)
ax_main.set_xlabel('Eje X')
ax_main.set_ylabel('Eje Y')
ax_main.set_title('Simulador de Trilateración - Comunicaciones Digitales UMNG - jose.rugeles@unimilitar.edu.co')

# Graficar los nodos fijos
ax_main.scatter(nodos_fijos[:, 0], nodos_fijos[:, 1], color='red', label='Nodos Fijos', s=150)

# Etiquetas para los nodos fijos
for i, nodo_fijo in enumerate(nodos_fijos):
    ax_main.text(nodo_fijo[0] + 0.1, nodo_fijo[1] + 0.1, etiquetas_nodos[i], fontsize=12, ha="left")

# Graficar el nodo móvil
nodo_movil_plot, = ax_main.plot([], [], 'bo', label='Nodo Móvil', markersize=12)

# Graficar los vectores de distancia (inicialmente vacíos)
vectores = [ax_main.plot([], [], 'k--')[0] for _ in nodos_fijos]

# Traza de la trayectoria del nodo móvil (en gris)
trayectoria, = ax_main.plot([], [], 'gray', alpha=0.3)

# Configurar los subplots de acelerómetro y giroscopio (como en el segundo código)
# Acelerómetro
ax_right2.set_xlim(0, 200)
ax_right2.set_ylim(-8, 8)  # Rango ajustado para las señales simuladas
ax_right2.set_title('Acelerómetro')
ax_right2.set_xlabel('Tiempo')
ax_right2.set_ylabel('Valor')
ax_right2.grid(True, alpha=0.3)

# Giroscopio
ax_right3.set_xlim(0, 200)
ax_right3.set_ylim(-8, 8)
ax_right3.set_title('Giroscopio')
ax_right3.set_xlabel('Tiempo')
ax_right3.set_ylabel('Valor')
ax_right3.grid(True, alpha=0.3)

# Inicializar las gráficas para los subgráficos de acelerómetro y giroscopio (tres ejes)
acelerometro_plots = []
giroscopio_plots = []
for i in range(3):
    acelerometro_plots.append(ax_right2.plot([], [], label=f'Acelerómetro {["X", "Y", "Z"][i]}', color=COLORES_SENSORES['acelerometro'][i])[0])
    giroscopio_plots.append(ax_right3.plot([], [], label=f'Giroscopio {["X", "Y", "Z"][i]}', color=COLORES_SENSORES['giroscopio'][i])[0])

# Agregar leyendas estáticas (como en el segundo código, pero sin actualizar en cada frame)
ax_right2.legend()
ax_right3.legend()

# Configurar el subplot de distancias históricas
ax_right1.axis('off')
ax_right1.set_title('Distancias Históricas', fontsize=12)

# Función de actualización de la animación
def actualizar(frame):
    global trayectoria_x, trayectoria_y

    # Mover el nodo móvil a lo largo de una trayectoria circular (como en el primer código)
    nodo_movil[0] = 5 + 3 * np.sin(frame * 0.1)
    nodo_movil[1] = 5 + 3 * np.cos(frame * 0.1)
    
    # Actualizar la posición del nodo móvil en la gráfica
    nodo_movil_plot.set_data([nodo_movil[0]], [nodo_movil[1]])

    # Agregar las coordenadas actuales a la trayectoria
    trayectoria_x.append(nodo_movil[0])
    trayectoria_y.append(nodo_movil[1])

    # Calcular las distancias a cada nodo fijo
    distancias = [calcular_distancia(nodo_movil, nodo_fijo) for nodo_fijo in nodos_fijos]
    
    # Actualizar los vectores de distancia desde cada nodo fijo
    for i, nodo_fijo in enumerate(nodos_fijos):
        vectores[i].set_data([nodo_fijo[0], nodo_movil[0]], [nodo_fijo[1], nodo_movil[1]])

    # Actualizar las distancias históricas
    for i, distancia in enumerate(distancias):
        distancias_historicas[f'R{i+1}'].append(distancia)

    # Borrar las etiquetas anteriores (excepto las de los nodos fijos)
    for label in ax_main.texts[4:]:  # Las primeras 4 son las etiquetas de los nodos
        label.set_visible(False)

    # Mostrar solo los nombres de los vectores sin las distancias
    for i, distancia in enumerate(distancias):
        ax_main.text((nodo_movil[0] + nodos_fijos[i][0]) / 2 + 0.2, 
                     (nodo_movil[1] + nodos_fijos[i][1]) / 2, 
                     f'R{i+1}', fontsize=10)

    # Actualizar las distancias históricas en el subplot de la derecha
    texto_historial = '\n'.join([f'{k}: {v[-1]:.2f}m' for k, v in distancias_historicas.items()])
    ax_right1.clear()
    ax_right1.axis('off')
    ax_right1.set_title('Distancias Históricas', fontsize=12)
    ax_right1.text(0.1, 0.8, texto_historial, fontsize=12, verticalalignment='top', horizontalalignment='left')

    # Actualizar la trayectoria en gris
    trayectoria.set_data(trayectoria_x, trayectoria_y)

    # Actualizar las señales del acelerómetro y giroscopio (tres ejes)
    if frame > 0:  # Evitar arrays vacíos cuando frame=0
        x_data = np.arange(frame)
        for i in range(3):
            acelerometro_plots[i].set_data(x_data, acelerometro[i, :frame])
            giroscopio_plots[i].set_data(x_data, giroscopio[i, :frame])
    else:
        for i in range(3):
            acelerometro_plots[i].set_data([], [])
            giroscopio_plots[i].set_data([], [])

    return [nodo_movil_plot, *vectores, trayectoria, *acelerometro_plots, *giroscopio_plots]

# Crear la animación
ani = animation.FuncAnimation(fig, actualizar, frames=200, interval=100, blit=False)

# Ajustar los márgenes manualmente si es necesario
plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

# Mostrar la animación
plt.show()