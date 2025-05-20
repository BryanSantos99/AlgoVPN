import json
import heapq
from threading import Thread
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import socket

class FileSenderFrame(ttk.LabelFrame):
    def __init__(self, parent, app_instance, graph_data, *args, **kwargs):
        super().__init__(parent, text="Envío Optimizado via Hamachi", *args, **kwargs)
        self.app = app_instance
        self.selected_file = None
        self.graph_data = graph_data  # Datos del grafo (JSON procesado)
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        # Campo para IP Hamachi del destino
        ttk.Label(self, text="IP Hamachi del Destino:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_ip = ttk.Entry(self)
        self.entry_ip.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.entry_ip.insert(0, "25.")  # Prefijo común en Hamachi

        # Selección de archivo
        self.file_frame = ttk.Frame(self)
        self.file_frame.grid(row=2, column=0, sticky="ew", pady=5)
        
        self.btn_select = ttk.Button(
            self.file_frame, 
            text="Seleccionar Archivo",
            command=self.select_file
        )
        self.btn_select.pack(side=tk.LEFT, padx=5)
        
        self.lbl_file = ttk.Label(self.file_frame, text="Ningún archivo seleccionado")
        self.lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Botón de envío optimizado
        self.btn_send = ttk.Button(
            self,
            text="Enviar Archivo (Ruta Óptima)",
            command=self.start_optimized_send_thread,
            state=tk.DISABLED
        )
        self.btn_send.grid(row=3, column=0, pady=10)

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Seleccionar archivo")
        if file_path:
            self.selected_file = file_path
            self.lbl_file.config(text=os.path.basename(file_path))
            self.btn_send['state'] = tk.NORMAL if self.entry_ip.get() else tk.DISABLED

    def dijkstra(self, graph, start):
        distances = {node: float('infinity') for node in graph}
        distances[start] = 0
        priority_queue = [(0, start)]
        previous_nodes = {node: None for node in graph}
        
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            
            if current_distance > distances[current_node]:
                continue
                
            for neighbor, weight in graph[current_node].items():
                distance = current_distance + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(priority_queue, (distance, neighbor))
        
        return distances, previous_nodes

    def get_shortest_path(self, previous_nodes, start, target):
        path = []
        current_node = target
        
        while current_node is not None:
            path.append(current_node)
            current_node = previous_nodes.get(current_node, None)
        
        path.reverse()
        return path if path[0] == start else []

    def build_graph_from_data(self):
        with open(self.graph_data, "r", encoding="utf-8") as f:
            graph_j = json.load(f)
        if isinstance(graph_j, str):
            try:    
                graph_j = json.loads(graph_j)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error al parsear JSON: {str(e)}")
    
        # Construir el grafo
        graph = {}
        
        # Iterar sobre cada test en los datos
        for test in graph_j.get('tests', []):
            results = test.get('results', {})
            nodes = list(results.keys())
            
            # Añadir todos los nodos al grafo
            for node in nodes:
                if node not in graph:
                    graph[node] = {}
                
                # Crear conexiones con otros nodos
                for other_node in nodes:
                    if other_node != node:
                        # Usar la latencia como peso
                        graph[node][other_node] = results[other_node]
        
        return graph

    def start_optimized_send_thread(self):
        ip_destino = self.entry_ip.get().strip()
        if not ip_destino:
            messagebox.showwarning("Error", "Ingresa la IP Hamachi del destino")
            return
            
        Thread(target=self.send_via_optimal_path, args=(ip_destino,), daemon=True).start()

    def send_via_optimal_path(self, target_ip):
        try:
            self.btn_send['state'] = tk.DISABLED
            
            # 1. Construir el grafo
            try:
                graph = self.build_graph_from_data()
            except Exception as e:
                raise ValueError(f"Error al construir el grafo: {str(e)}")
            
            # 2. Obtener IP local (puede no estar en el grafo)
            local_ip = socket.gethostbyname(socket.gethostname())
            
            # 3. Si nuestra IP no está en el grafo, seleccionar el nodo con mejor conexión promedio
            if local_ip not in graph:
                # Calcular nodo con mejor latencia promedio
                best_node = min(
                    graph.keys(),
                    key=lambda node: sum(graph[node].values()) / len(graph[node])
                )
                local_ip = best_node
                self.app.log(f"Nota: IP local no encontrada en grafo, usando nodo óptimo: {local_ip}")
            
            # 4. Calcular ruta óptima
            distances, previous_nodes = self.dijkstra(graph, local_ip)
            path = self.get_shortest_path(previous_nodes, local_ip, target_ip)
            
            if not path:
                raise ValueError(f"No se encontró ruta válida a {target_ip}")
            
            self.app.log(f"\nRuta óptima encontrada: {' -> '.join(path)}")
            self.app.log(f"Latencia total estimada: {distances[target_ip]:.2f} ms")
            
            # 5. Enviar archivo (implementación simplificada)
            self.send_file_to_node(target_ip)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular ruta: {str(e)}")
            self.app.log(f"Error: {str(e)}")
        finally:
            self.btn_send['state'] = tk.NORMAL

    def send_file_to_node(self, ip_destino):
        try:
            self.app.log(f"\nConectando a {ip_destino} via Hamachi...")
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(15)
                s.connect((ip_destino, 8080))
                
                filename = os.path.basename(self.selected_file)
                filesize = os.path.getsize(self.selected_file)
                s.sendall(f"{filename}|{filesize}".encode())
                
                with open(self.selected_file, 'rb') as f:
                    while True:
                        data = f.read(4096)
                        if not data:
                            break
                        s.sendall(data)
            
            messagebox.showinfo("Éxito", f"Archivo enviado a {ip_destino}")
            self.app.log(f"¡{filename} ({filesize/1024:.2f} KB) enviado via ruta óptima!")
            
        except socket.timeout:
            messagebox.showerror("Error", "Timeout: Verifica la IP y conexión Hamachi")
            self.app.log("Error: ¿El receptor está ejecutando el script?")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo en el envío: {str(e)}")
            self.app.log(f"Error: {str(e)}")