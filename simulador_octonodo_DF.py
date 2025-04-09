"""
Simulador de Trilateración con Configuración Octonodal (Sin Estimación)
--------------------------------------------------------------------
Este código implementa un simulador de trilateración con ocho nodos fijos
dispuestos en forma circular equiespaciados y un nodo móvil externo.

Características:
1. Ocho nodos de referencia en configuración circular
2. Nodo móvil con trayectoria exterior
3. Visualización de distancias y RSSI
4. Sensores inerciales simulados

Autor: jose.rugeles@unimilitar.edu.co
Universidad Militar Nueva Granada
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
from matplotlib.widgets import CheckButtons
import sys

# Configuración del backend para evitar problemas en algunos entornos
plt.switch_backend('TkAgg')

class SimuladorTrilateracion:
    """
    Clase principal del simulador de trilateración.
    Implementa un sistema de localización basado en distancias a nodos de referencia.
    """
    
    def __init__(self):
        """Inicializa el simulador con la configuración predeterminada."""
        # Parámetros de radio para el sistema de Direction Finding
        self.frecuencia_ghz = 2.4  # Frecuencia WiFi en GHz
        self.lambda_m = (3e8) / (self.frecuencia_ghz * 1e9)  # Longitud de onda en metros
        self.separacion_lambda = 2  # Separación en múltiplos de longitud de onda (2λ)
        
        # Calcular el radio basado en la longitud de onda deseada para los 8 nodos
        self.radio_nodos = (self.separacion_lambda * self.lambda_m) / (2 * np.sin(np.pi / 8))
        self.centro_nodos = np.array([0, 0])  # Centro del círculo de nodos fijos
        self.num_nodos = 8  # Número de nodos fijos
        
        # Generar las posiciones de los nodos fijos en círculo
        self.nodos_fijos = self.generar_nodos_circulares()
        
        # Definir el nodo móvil (inicia más lejos del círculo)
        self.nodo_movil = np.array([self.radio_nodos * 3.0, 0])
        
        # Configuración de la trayectoria
        self.radio_trayectoria = self.radio_nodos * 2.5
        self.velocidad_trayectoria = 0.03
        self.centro_trayectoria = self.centro_nodos
        
        # Historial de posiciones y distancias
        self.distancias_historicas = {f'R{i+1}': [] for i in range(self.num_nodos)}
        self.trayectoria_x = []
        self.trayectoria_y = []
        
        # Vectores de dirección y magnitudes RSSI
        self.vectores_direccion = np.zeros((self.num_nodos, 2))
        self.magnitudes_rssi = np.zeros(self.num_nodos)
        
        # Parámetros para el modelo de pérdida de trayectoria RSSI
        self.potencia_tx = 0
        self.perdida_ref = 40
        self.exponente_perdida = 2
        
        # Error de medición para simular ruido en las distancias
        self.error_medicion = 0.2
        
        # Para visualización selectiva de elementos
        self.mostrar_vectores = True
        self.mostrar_trayectoria = True
        
        # Generar señales simuladas para el acelerómetro y el giroscopio
        np.random.seed(42)
        self.max_frames = 300
        self.acelerometro = 0.5 * np.cumsum(np.random.randn(3, self.max_frames), axis=1)
        self.giroscopio = 0.3 * np.cumsum(np.random.randn(3, self.max_frames), axis=1)
        
        # Colores para los sensores
        self.colores_sensores = {
            'acelerometro': ['#d73027', '#fc8d59', '#fee090'],
            'giroscopio': ['#4575b4', '#91bfdb', '#e0f3f8']
        }
        
        # Estado de la animación
        self.pausa = False
        self.frame_actual = 0
        
        # Inicializar la figura y los ejes
        self.crear_interfaz()
    
    def generar_nodos_circulares(self):
        """Genera las posiciones de los nodos fijos en un círculo."""
        angulos = np.linspace(0, 2*np.pi, self.num_nodos, endpoint=False)
        x = self.centro_nodos[0] + self.radio_nodos * np.cos(angulos)
        y = self.centro_nodos[1] + self.radio_nodos * np.sin(angulos)
        return np.column_stack((x, y))
    
    def calcular_distancia(self, p1, p2):
        """Calcula la distancia euclidiana entre dos puntos 2D."""
        return np.sqrt(np.sum((p1 - p2)**2))
    
    def calcular_vector_direccion(self, origen, destino):
        """Calcula el vector de dirección normalizado desde origen hacia destino."""
        vector = destino - origen
        magnitud = np.linalg.norm(vector)
        if magnitud > 0:
            vector_normalizado = vector / magnitud
        else:
            vector_normalizado = np.array([0, 0])
        return vector_normalizado, magnitud
    
    def calcular_rssi(self, distancia):
        """Calcula el RSSI basado en un modelo de pérdida de trayectoria."""
        if distancia > 0:
            rssi = self.potencia_tx - (self.perdida_ref + 10 * self.exponente_perdida * np.log10(distancia))
            rssi += np.random.normal(0, 2)
        else:
            rssi = self.potencia_tx
        return rssi

    def calcular_vector_resultante(self, vectores, pesos):
        """Calcula el vector resultante ponderado basado en los vectores y sus pesos."""
        pesos_lineales = np.power(10, pesos/10)
        resultante = np.zeros(2)
        for i, vector in enumerate(vectores):
            resultante += vector * pesos_lineales[i]
        magnitud = np.linalg.norm(resultante)
        if magnitud > 0:
            resultante /= magnitud
        return resultante
    
    def crear_interfaz(self):
        """Crea la interfaz gráfica del simulador."""
        # Crear la figura con GridSpec
        self.fig = plt.figure(figsize=(15, 8))
        
        # Configuración de la cuadrícula
        self.grid = plt.GridSpec(3, 4, wspace=0.3, hspace=0.3)
        
        # Subplot principal (izquierda)
        self.ax_main = self.fig.add_subplot(self.grid[:, :3])
        
        # Subplots a la derecha
        self.ax_right1 = self.fig.add_subplot(self.grid[0, 3])  # Distancias
        self.ax_right2 = self.fig.add_subplot(self.grid[1, 3])  # Acelerómetro
        self.ax_right3 = self.fig.add_subplot(self.grid[2, 3])  # Giroscopio
        
        # Configurar el subplot principal
        limite_x = self.radio_trayectoria * 1.2
        limite_y = self.radio_trayectoria * 1.2
        self.ax_main.set_xlim(-limite_x, limite_x)
        self.ax_main.set_ylim(-limite_y, limite_y)
        self.ax_main.set_xlabel('Eje X (m)')
        self.ax_main.set_ylabel('Eje Y (m)')
        self.ax_main.set_title(f'Simulador de Direction Finding - WiFi {self.frecuencia_ghz} GHz (λ={self.lambda_m*100:.1f}cm)', fontsize=14)
        
        # Configurar la cuadrícula principal
        self.ax_main.grid(True, alpha=0.3, linestyle='--', color='gray')
        
        # Marcar el origen
        self.ax_main.plot(0, 0, 'k+', markersize=12, markeredgewidth=2, zorder=15)
        
        # Círculo base
        circulo_base = plt.Circle(self.centro_nodos, self.radio_nodos, 
                                fill=False, color='blue', linestyle='-', alpha=0.6)
        self.ax_main.add_artist(circulo_base)
        
        # Nodos fijos
        self.ax_main.scatter(self.nodos_fijos[:, 0], self.nodos_fijos[:, 1], 
                           color='red', label='Nodos Fijos', s=100, zorder=10)
        
        # Etiquetas de nodos
        for i, nodo_fijo in enumerate(self.nodos_fijos):
            angulo = 2 * np.pi * i / self.num_nodos
            dx = (self.radio_nodos * 0.25) * np.cos(angulo)
            dy = (self.radio_nodos * 0.25) * np.sin(angulo)
            self.ax_main.text(nodo_fijo[0] + dx, nodo_fijo[1] + dy, 
                            f'N{i+1}\n({nodo_fijo[0]:.2f}, {nodo_fijo[1]:.2f})', 
                            fontsize=8, ha="center", va="center",
                            bbox=dict(facecolor='white', alpha=0.7))
        
        # Nodo móvil
        self.nodo_movil_plot, = self.ax_main.plot([], [], 'bo', 
                                                label='Nodo Móvil Real', 
                                                markersize=12, zorder=5)
        
        # Vectores de distancia
        self.vectores = [self.ax_main.plot([], [], 'k--', alpha=0.3)[0] 
                        for _ in range(self.num_nodos)]
        
        # Trayectoria real
        self.trayectoria_real, = self.ax_main.plot([], [], 'gray', alpha=0.5, 
                                                  label='Trayectoria Real')
        
        # Leyenda
        self.ax_main.legend(loc='upper right', fontsize=9, 
                           frameon=True, fancybox=True)
        
        # Configurar subplots secundarios
        self.configurar_subplot_distancias()
        self.configurar_subplot_acelerometro()
        self.configurar_subplot_giroscopio()
        
        # Checkbox para elementos visuales
        ax_check = plt.axes([0.05, 0.02, 0.13, 0.07])
        self.check_elementos = CheckButtons(
            ax_check, ['Vectores', 'Trayectoria'], 
            [True, True]
        )
        self.check_elementos.on_clicked(self.toggle_elementos)
        
        # Forzar el dibujado inicial
        self.fig.canvas.draw()
    
    def configurar_subplot_distancias(self):
        """Configura el subplot de distancias."""
        self.ax_right1.axis('off')
        self.ax_right1.set_title('Distancias y RSSI a Nodos', fontsize=10)
    
    def configurar_subplot_acelerometro(self):
        """Configura el subplot del acelerómetro."""
        self.ax_right2.set_xlim(0, 100)
        self.ax_right2.set_ylim(-5, 5)
        self.ax_right2.set_title('Acelerómetro (m/s²)', fontsize=10)
        self.ax_right2.set_xlabel('Tiempo (s)', fontsize=8)
        self.ax_right2.grid(True, alpha=0.3)
        
        self.acelerometro_plots = []
        for i in range(3):
            self.acelerometro_plots.append(
                self.ax_right2.plot([], [], 
                                  label=f'{["X", "Y", "Z"][i]}', 
                                  color=self.colores_sensores['acelerometro'][i])[0]
            )
        self.ax_right2.legend(fontsize=8)
    
    def configurar_subplot_giroscopio(self):
        """Configura el subplot del giroscopio."""
        self.ax_right3.set_xlim(0, 100)
        self.ax_right3.set_ylim(-5, 5)
        self.ax_right3.set_title('Giroscopio (°/s)', fontsize=10)
        self.ax_right3.set_xlabel('Tiempo (s)', fontsize=8)
        self.ax_right3.grid(True, alpha=0.3)
        
        self.giroscopio_plots = []
        for i in range(3):
            self.giroscopio_plots.append(
                self.ax_right3.plot([], [], 
                                  label=f'{["X", "Y", "Z"][i]}', 
                                  color=self.colores_sensores['giroscopio'][i])[0]
            )
        self.ax_right3.legend(fontsize=8)
    
    def toggle_elementos(self, label):
        """Callback para mostrar/ocultar elementos visuales."""
        if label == 'Vectores':
            self.mostrar_vectores = not self.mostrar_vectores
        elif label == 'Trayectoria':
            self.mostrar_trayectoria = not self.mostrar_trayectoria
    
    def actualizar_frame(self, frame):
        """Actualiza la animación."""
        if self.pausa:
            return self.elementos_actuales
        
        # Mover el nodo móvil
        self.nodo_movil[0] = self.centro_trayectoria[0] + self.radio_trayectoria * np.sin(frame * self.velocidad_trayectoria)
        self.nodo_movil[1] = self.centro_trayectoria[1] + self.radio_trayectoria * np.cos(frame * self.velocidad_trayectoria)
        
        # Actualizar posición del nodo móvil
        self.nodo_movil_plot.set_data([self.nodo_movil[0]], [self.nodo_movil[1]])
        
        # Actualizar trayectoria
        self.trayectoria_x.append(self.nodo_movil[0])
        self.trayectoria_y.append(self.nodo_movil[1])
        
        # Calcular distancias y RSSI
        distancias_reales = [self.calcular_distancia(self.nodo_movil, nodo_fijo) for nodo_fijo in self.nodos_fijos]
        distancias_medidas = [d + np.random.normal(0, self.error_medicion) for d in distancias_reales]
        
        # Actualizar vectores de dirección y RSSI
        for i, nodo_fijo in enumerate(self.nodos_fijos):
            self.vectores_direccion[i], _ = self.calcular_vector_direccion(nodo_fijo, self.nodo_movil)
            self.magnitudes_rssi[i] = self.calcular_rssi(distancias_medidas[i])
        
        # Actualizar vectores de distancia
        for i, nodo_fijo in enumerate(self.nodos_fijos):
            if self.mostrar_vectores:
                self.vectores[i].set_data([nodo_fijo[0], self.nodo_movil[0]], 
                                        [nodo_fijo[1], self.nodo_movil[1]])
            else:
                self.vectores[i].set_data([], [])
        
        # Actualizar distancias históricas
        for i, distancia in enumerate(distancias_medidas):
            self.distancias_historicas[f'R{i+1}'].append(distancia)
        
        # Limpiar textos anteriores
        for text in self.ax_right1.texts:
            text.remove()
        
        # Calcular vector resultante y ángulo
        vector_resultante = self.calcular_vector_resultante(self.vectores_direccion, self.magnitudes_rssi)
        angulo_resultante = np.arctan2(vector_resultante[1], vector_resultante[0]) * 180 / np.pi
        
        # Crear texto de información
        texto_distancias = ''
        for i, (distancia, rssi) in enumerate(zip(distancias_medidas, self.magnitudes_rssi)):
            texto_distancias += f'R{i+1}: {distancia:.2f} m | RSSI: {rssi:.1f} dBm | ({self.vectores_direccion[i][0]:.2f}, {self.vectores_direccion[i][1]:.2f})\n'
        
        texto_info = f'\nNodo móvil: ({self.nodo_movil[0]:.2f}, {self.nodo_movil[1]:.2f})\n'
        texto_info += f'Vector de dirección: [{vector_resultante[0]:.2f}, {vector_resultante[1]:.2f}]\n'
        texto_info += f'Ángulo: {angulo_resultante:.1f}°'
        
        # Mostrar texto actualizado
        texto = self.ax_right1.text(0.05, 0.95, texto_distancias + texto_info, 
                                  fontsize=8, verticalalignment='top',
                                  transform=self.ax_right1.transAxes,
                                  bbox=dict(boxstyle="round,pad=0.3", 
                                          fc="white", ec="gray", alpha=0.7))
        
        # Actualizar trayectoria
        max_puntos = 200
        if self.mostrar_trayectoria:
            self.trayectoria_real.set_data(self.trayectoria_x[-max_puntos:], 
                                         self.trayectoria_y[-max_puntos:])
        else:
            self.trayectoria_real.set_data([], [])
        
        # Actualizar sensores
        if frame > 0:
            tiempo = np.arange(frame + 1)
            for i in range(3):
                self.acelerometro_plots[i].set_data(tiempo, self.acelerometro[i, :frame+1])
                self.giroscopio_plots[i].set_data(tiempo, self.giroscopio[i, :frame+1])
            
            self.ax_right2.relim()
            self.ax_right2.autoscale_view()
            self.ax_right3.relim()
            self.ax_right3.autoscale_view()
        
        # Forzar actualización del canvas
        self.fig.canvas.draw()
        
        # Guardar elementos actuales
        self.elementos_actuales = [self.nodo_movil_plot,
                                 self.trayectoria_real, *self.vectores,
                                 *self.acelerometro_plots, *self.giroscopio_plots,
                                 texto]
        
        return self.elementos_actuales
    
    def iniciar_animacion(self):
        """Inicia la animación del simulador."""
        self.ani = animation.FuncAnimation(
            self.fig, self.actualizar_frame, 
            frames=self.max_frames, interval=100,
            blit=True,
            repeat=False,
            cache_frame_data=False
        )
        
        plt.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.05, wspace=0.3, hspace=0.3)
        plt.show()

def main():
    """Función principal para iniciar el simulador."""
    print("Iniciando Simulador de Trilateración - Configuración Octonodal (Sin Estimación)...")
    print("Controles disponibles:")
    print("- Casillas para mostrar/ocultar elementos visuales")
    
    simulador = SimuladorTrilateracion()
    simulador.iniciar_animacion()

if __name__ == "__main__":
    main() 