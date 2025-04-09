"""
Simulador de Localización en Espacios Cerrados
--------------------------------------------
Este código implementa un simulador de localización para espacios cerrados con:
- Paredes y pasillos interiores
- Modelo de propagación de señal para interiores
- Ruido específico de ambientes cerrados
- Visualización de la calidad de la señal

Autor: jose.rugeles@unimilitar.edu.co
Universidad Militar Nueva Granada
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Circle
import sys

# Configuración del backend
plt.switch_backend('TkAgg')

class SimuladorLocalizacionInteriores:
    def __init__(self):
        # Dimensiones del espacio interior (en metros)
        self.ancho = 20
        self.alto = 15
        
        # Definir paredes y pasillos
        self.paredes = [
            # Paredes exteriores
            Rectangle((0, 0), self.ancho, 0.2, color='gray'),  # Pared inferior
            Rectangle((0, 0), 0.2, self.alto, color='gray'),   # Pared izquierda
            Rectangle((0, self.alto-0.2), self.ancho, 0.2, color='gray'),  # Pared superior
            Rectangle((self.ancho-0.2, 0), 0.2, self.alto, color='gray'),  # Pared derecha
            
            # Paredes interiores (habitaciones)
            Rectangle((2, 2), 5, 4, color='lightgray'),  # Habitación 1
            Rectangle((9, 2), 5, 4, color='lightgray'),  # Habitación 2
            Rectangle((2, 9), 5, 4, color='lightgray'),  # Habitación 3
            Rectangle((9, 9), 5, 4, color='lightgray'),  # Habitación 4
            
            # Pared central
            Rectangle((7, 2), 0.2, 11, color='gray'),  # Pared vertical central
            Rectangle((2, 7), 16, 0.2, color='gray'),  # Pared horizontal central
        ]
        
        # Definir las posiciones de los nodos fijos (en 2D) - en los pasillos
        self.nodos_fijos = np.array([
            [1, 1],           # Esquina inferior izquierda (pasillo)
            [self.ancho-1, 1],  # Esquina inferior derecha (pasillo)
            [self.ancho-1, self.alto-1],  # Esquina superior derecha (pasillo)
            [1, self.alto-1]    # Esquina superior izquierda (pasillo)
        ])
        
        # Etiquetas para los nodos
        self.etiquetas_nodos = ['AP1', 'AP2', 'AP3', 'AP4']
        
        # Definir el nodo móvil (inicia en el centro del pasillo)
        self.nodo_movil = np.array([self.ancho/2, self.alto/2])
        
        # Parámetros del modelo de propagación
        self.n = 2.5  # Exponente de pérdida de propagación (típico para interiores)
        self.sigma = 3.0  # Desviación estándar del ruido (dB)
        
        # Historial de distancias y RSSI
        self.distancias_historicas = {f'R{i+1}': [] for i in range(len(self.nodos_fijos))}
        self.rssi_historicos = {f'RSSI{i+1}': [] for i in range(len(self.nodos_fijos))}
        
        # Lista para la trayectoria
        self.trayectoria_x = []
        self.trayectoria_y = []
        
        # Crear la figura y los ejes
        self.crear_interfaz()
    
    def calcular_distancia_con_obstaculos(self, p1, p2):
        """Calcula la distancia considerando obstáculos."""
        # Por ahora, implementación simple. Se puede mejorar con algoritmos de pathfinding
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def calcular_rssi(self, distancia):
        """Calcula el RSSI basado en el modelo de propagación para interiores."""
        # RSSI = -10 * n * log10(d) + X
        # donde n es el exponente de pérdida y X es el ruido
        rssi_base = -10 * self.n * np.log10(distancia)
        ruido = np.random.normal(0, self.sigma)
        return rssi_base + ruido
    
    def crear_interfaz(self):
        """Crea la interfaz gráfica del simulador."""
        self.fig = plt.figure(figsize=(15, 8))
        self.grid = plt.GridSpec(2, 3, wspace=0.3, hspace=0.3)
        
        # Subplot principal
        self.ax_main = self.fig.add_subplot(self.grid[:, :2])
        
        # Subplots secundarios
        self.ax_rssi = self.fig.add_subplot(self.grid[0, 2])
        self.ax_distancias = self.fig.add_subplot(self.grid[1, 2])
        
        # Configurar el subplot principal
        self.ax_main.set_xlim(0, self.ancho)
        self.ax_main.set_ylim(0, self.alto)
        self.ax_main.set_xlabel('X (m)')
        self.ax_main.set_ylabel('Y (m)')
        self.ax_main.set_title('Simulador de Localización en Edificio con Pasillos')
        
        # Dibujar paredes y obstáculos
        for pared in self.paredes:
            self.ax_main.add_patch(pared)
        
        # Graficar los nodos fijos
        self.ax_main.scatter(self.nodos_fijos[:, 0], self.nodos_fijos[:, 1], 
                           color='red', label='APs', s=150)
        
        # Etiquetas para los nodos
        for i, nodo in enumerate(self.nodos_fijos):
            self.ax_main.text(nodo[0] + 0.3, nodo[1] + 0.3, 
                            self.etiquetas_nodos[i], fontsize=10)
        
        # Inicializar elementos móviles
        self.nodo_movil_plot, = self.ax_main.plot([], [], 'bo', 
                                                 label='Dispositivo Móvil', markersize=12)
        self.vectores = [self.ax_main.plot([], [], 'k--')[0] 
                        for _ in self.nodos_fijos]
        self.trayectoria, = self.ax_main.plot([], [], 'gray', alpha=0.3)
        
        # Configurar subplots secundarios
        self.configurar_subplots()
        
        # Añadir leyenda
        self.ax_main.legend(loc='upper right')
    
    def configurar_subplots(self):
        """Configura los subplots secundarios."""
        # Subplot de RSSI
        self.ax_rssi.set_title('RSSI en tiempo real')
        self.ax_rssi.set_xlabel('Tiempo')
        self.ax_rssi.set_ylabel('RSSI (dBm)')
        self.ax_rssi.grid(True)
        
        # Subplot de distancias
        self.ax_distancias.set_title('Distancias a los APs')
        self.ax_distancias.set_xlabel('Tiempo')
        self.ax_distancias.set_ylabel('Distancia (m)')
        self.ax_distancias.grid(True)
        
        # Inicializar líneas para RSSI y distancias
        self.rssi_lines = []
        self.distancia_lines = []
        
        for i in range(len(self.nodos_fijos)):
            # Líneas para RSSI
            rssi_line, = self.ax_rssi.plot([], [], 
                                          label=f'AP{i+1}', 
                                          color=plt.cm.tab10(i))
            self.rssi_lines.append(rssi_line)
            
            # Líneas para distancias
            dist_line, = self.ax_distancias.plot([], [], 
                                               label=f'R{i+1}', 
                                               color=plt.cm.tab10(i))
            self.distancia_lines.append(dist_line)
        
        self.ax_rssi.legend()
        self.ax_distancias.legend()
    
    def actualizar(self, frame):
        """Actualiza la animación."""
        # Mover el nodo móvil por los pasillos
        # Trayectoria que sigue los pasillos
        if frame < 50:
            # Movimiento horizontal en el pasillo inferior
            self.nodo_movil[0] = 1 + (frame / 50) * (self.ancho - 2)
            self.nodo_movil[1] = 1
        elif frame < 100:
            # Movimiento vertical en el pasillo derecho
            self.nodo_movil[0] = self.ancho - 1
            self.nodo_movil[1] = 1 + ((frame - 50) / 50) * (self.alto - 2)
        elif frame < 150:
            # Movimiento horizontal en el pasillo superior
            self.nodo_movil[0] = self.ancho - 1 - ((frame - 100) / 50) * (self.ancho - 2)
            self.nodo_movil[1] = self.alto - 1
        else:
            # Movimiento vertical en el pasillo izquierdo
            self.nodo_movil[0] = 1
            self.nodo_movil[1] = self.alto - 1 - ((frame - 150) / 50) * (self.alto - 2)
        
        # Actualizar posición del nodo móvil
        self.nodo_movil_plot.set_data([self.nodo_movil[0]], [self.nodo_movil[1]])
        
        # Actualizar trayectoria
        self.trayectoria_x.append(self.nodo_movil[0])
        self.trayectoria_y.append(self.nodo_movil[1])
        self.trayectoria.set_data(self.trayectoria_x, self.trayectoria_y)
        
        # Calcular distancias y RSSI
        for i, nodo_fijo in enumerate(self.nodos_fijos):
            # Calcular distancia
            distancia = self.calcular_distancia_con_obstaculos(self.nodo_movil, nodo_fijo)
            self.distancias_historicas[f'R{i+1}'].append(distancia)
            
            # Calcular RSSI
            rssi = self.calcular_rssi(distancia)
            self.rssi_historicos[f'RSSI{i+1}'].append(rssi)
            
            # Actualizar vector de distancia
            self.vectores[i].set_data([nodo_fijo[0], self.nodo_movil[0]], 
                                     [nodo_fijo[1], self.nodo_movil[1]])
            
            # Actualizar gráfica de RSSI
            self.rssi_lines[i].set_data(range(len(self.rssi_historicos[f'RSSI{i+1}'])), 
                                      self.rssi_historicos[f'RSSI{i+1}'])
            
            # Actualizar gráfica de distancias
            self.distancia_lines[i].set_data(range(len(self.distancias_historicas[f'R{i+1}'])), 
                                           self.distancias_historicas[f'R{i+1}'])
        
        # Actualizar límites de los subplots
        self.ax_rssi.relim()
        self.ax_rssi.autoscale_view()
        self.ax_distancias.relim()
        self.ax_distancias.autoscale_view()
        
        return [self.nodo_movil_plot, *self.vectores, self.trayectoria, 
                *self.rssi_lines, *self.distancia_lines]
    
    def iniciar(self):
        """Inicia la animación."""
        ani = animation.FuncAnimation(self.fig, self.actualizar, 
                                    frames=200, interval=50, blit=True)
        plt.show()

# Crear y ejecutar el simulador
if __name__ == "__main__":
    simulador = SimuladorLocalizacionInteriores()
    simulador.iniciar() 