import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
import threading
import subprocess
import os
import random
import heapq
import json
from PIL import Image
import time
import sys
import queue
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import servidor
from http.server import SimpleHTTPRequestHandler, HTTPServer
from PyQt5.QtCore import QTimer
from enviar import FileSenderFrame
import recibir

class AlgoVPNApp:
    def __init__(self, root):
        self.log_queue = queue.Queue()
        self.root = root
        root.title("AlgoVPN - Monitor de Red")
        self.TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "archivos_prueba")
        
        # Config paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.server_path = os.path.join(self.base_dir, "vpn", "servidor.py")
        self.latency_path = os.path.join(self.base_dir, "vpn", "latencia.py")
        self.bandwidth_path = os.path.join(self.base_dir, "vpn", "anchoBanda.py")
        self.results_dir = os.path.join(self.base_dir, "..", "docs", "resultados")
        self.test_files_dir = os.path.join(self.base_dir, "..", "archivos_prueba")
        self.graph_output = os.path.join(self.base_dir, "..", "grafo_ancho_banda.png")
        
        # Create directories
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.test_files_dir, exist_ok=True)
        
        # Setup UI
        self.setup_ui()
        
        # Control variables
        self.server_process = None
        self.graph_canvas = None
        self.bandwidth_timer = None
        
        

    def setup_ui(self):
        # Main container with scrollbar
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.main_container)
        self.scrollbar = ttk.Scrollbar(self.main_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Setup content
        self._setup_content()
        

    def run_bandwidth_test(self):
        self.clear_results()
        self.log("\nEjecutando prueba de ancho de banda...")
        subprocess.run(["python", self.bandwidth_path], cwd=os.path.dirname(self.bandwidth_path))
        def process_log_queue(self):
            """Procesa los mensajes en cola desde el hilo principal"""
            while not self.log_queue.empty():
                try:
                    message = self.log_queue.get_nowait()
                    self._safe_log(message)
                except queue.Empty:
                    break
            self.root.after(100, self.process_log_queue)  # Programar el próximo chequeo
    
    def _safe_log(self, message):
        """Método seguro para logging desde el hilo principal"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()

        
    def start_http_server(self):
        """Inicia el servidor HTTP en un hilo separado"""
        def run_server():
            servidor.create_test_file()
            self.server = HTTPServer(("0.0.0.0", 8080), servidor.Handler)
            self.log(f"Servidor HTTP iniciado en http://localhost:{8080}")
            self.log(f"Sirviendo archivos desde: {self.TEST_DIR}")
            self.server.serve_forever()
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
    def stop_http_server(self):
        """Detiene el servidor HTTP"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.log("Servidor HTTP detenido")
    def on_closing(self):
        """Maneja el evento de cierre de la ventana"""
        if messagebox.askokcancel("Salir", "¿Está seguro que desea salir?"):
            self.stop_http_server()
            self.stop_server()  
            # Detener cualquier otro proceso
            self.root.quit()
                
    def setup_ui(self):
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel de botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            btn_frame, 
            text="Ejecutar Pruebas Completas", 
            command=self.run_full_test,
            style='TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Prueba de Latencia", 
            command=self.run_latency_test
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Prueba de Ancho de Banda", 
            command=self.run_bandwidth_test
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Mostrar Gráfico", 
            command=self.show_graph
        ).pack(side=tk.LEFT, padx=5)
        
        # Panel de resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.results_text = tk.Text(
            results_frame, 
            height=10,
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        scrollbar = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        self.results_text.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Panel del gráfico
        graph_frame = ttk.LabelFrame(main_frame, text="Topología de Red", padding="10")
        graph_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.graph_label = ttk.Label(graph_frame, text="El gráfico aparecerá aquí después de las pruebas")
        self.graph_label.pack(expand=True)

        # Añadir el frame de envío de archivos
        self.file_sender = FileSenderFrame(main_frame, self, padding="10")
        self.file_sender.pack(fill=tk.X, pady=10)
            # Conectar señales si es necesario
        
        # Añadir el frame de recepción de archivos
        self.file_receiver = recibir.FileReceiverWidget(main_frame,port=8080)
        self.file_receiver.pack(fill=tk.X, pady=10)
       
        # Configurar estilo
        style = ttk.Style()
        style.configure('TButton', font=('Arial', 10, 'bold'))
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
       
        
    def log(self, message):
        """Agrega un mensaje a la cola para ser procesado por el hilo principal"""
        self.log_queue.put(message)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()
    
    def run_full_test(self):
        self.clear_results()
        threading.Thread(target=self._run_full_test, daemon=True).start()
    
    def _run_full_test(self):
        try:
            self.clear_results()
            self.log("Iniciando pruebas completas...")
            
            # 1. Crear archivo de prueba si no existe
            test_file = os.path.join(self.test_files_dir, "10MB.bin")
            if not os.path.exists(test_file):
                self.log("Generando archivo de prueba 10MB.bin...")
                self.generate_test_file()
            
            # 2. Iniciar servidor
            self.log("Iniciando servidor HTTP...")
            self.start_server()
            time.sleep(2)  # Esperar a que el servidor inicie
            
            # 3. Ejecutar pruebas de latencia
            self.log("\nEjecutando prueba de latencia...")
            subprocess.run(["python", self.latency_path], cwd=os.path.dirname(self.latency_path))
            
            # 4. Ejecutar pruebas de ancho de banda
            self.log("\nEjecutando prueba de ancho de banda...")
            subprocess.run(["python", self.bandwidth_path], cwd=os.path.dirname(self.bandwidth_path))
            
            # 5. Generar gráfico
            self.log("\nGenerando visualización de red...")
            self.generate_network_graph()
            
            self.log("\n¡Todas las pruebas completadas!")
        except Exception as e:
            self.log(f"\nError: {str(e)}")
        finally:
            self.stop_server()
    
    def generate_test_file(self):
        try:
            chunk_size = 1024 * 1024  # 1MB
            with open(os.path.join(self.test_files_dir, "10MB.bin"), 'wb') as f:
                for _ in range(10):  # 10MB
                    f.write(random.randbytes(chunk_size))
            self.log("Archivo de prueba creado exitosamente")
        except Exception as e:
            raise Exception(f"Error al crear archivo: {str(e)}")
    
    def start_server(self):
        try:
            self.server_process = subprocess.Popen(
                ["python", self.server_path],
                cwd=os.path.dirname(self.server_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            raise Exception(f"Error al iniciar servidor: {str(e)}")
    
    def stop_server(self):
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()
            finally:
                self.server_process = None
    
    def dijkstra(self,grafo, inicio):
        distancias = {nodo: float('inf') for nodo in grafo}
        distancias[inicio] = 0
        cola = [(0, inicio)]
        caminos = {inicio: []}  # Para guardar los caminos
        
        while cola:
            dist_actual, nodo_actual = heapq.heappop(cola)
            for vecino, datos in grafo[nodo_actual].items():
                peso = datos.get('weight', 1)  # Usamos el peso de la arista
                distancia = dist_actual + peso
                if distancia < distancias[vecino]:
                    distancias[vecino] = distancia
                    caminos[vecino] = caminos[nodo_actual] + [(nodo_actual, vecino)]
                    heapq.heappush(cola, (distancia, vecino))
        return distancias, caminos

    def generate_network_graph(self):
        """Genera un gráfico de red completo con manejo de direcciones IP y rutas óptimas"""
        try:
            # 1. Cargar y validar datos
            json_path = os.path.join(self.results_dir, "resultados_ancho_banda.json")
            if not os.path.exists(json_path):
                raise FileNotFoundError("Archivo de resultados no encontrado")
            
            with open(json_path, "r") as f:
                data = json.load(f)
            
            if not data.get("datos"):
                raise ValueError("Datos de ancho de banda no válidos")

            # 2. Sanitizar nombres de nodos (manejar IPs)
            sanitized_nodes = {}
            node_mapping = {}  # Para mapeo entre nombres sanitizados y originales
            for ip, speed in data["datos"].items():
                clean_name = f"node_{ip.replace('.', '_')}" if '.' in ip else ip
                sanitized_nodes[clean_name] = speed
                node_mapping[clean_name] = ip

            # 3. Crear grafo de red
            G = nx.Graph()
            origin_node = "Nodo_Origen"
            G.add_node(origin_node, 
                    color='green', 
                    size=1200,
                    original_name="Origen")

            # 4. Agregar nodos y conexiones
            for node, speed in sanitized_nodes.items():
                # Agregar nodo con metadatos
                G.add_node(node, 
                        original_name=node_mapping[node],
                        speed=speed)
                
                # Conexión con el nodo origen
                weight = 1/speed if speed not in (0, float('inf')) else float('inf')
                G.add_edge(origin_node, node, 
                        weight=weight,
                        original_speed=speed,
                        label=f"{speed:.2f} Mbps" if speed != float('inf') else "∞")
                
                # Conexiones entre nodos
                for other_node, other_speed in sanitized_nodes.items():
                    if node != other_node:
                        combined_speed = min(speed, other_speed)
                        weight = 1/combined_speed if combined_speed not in (0, float('inf')) else float('inf')
                        G.add_edge(node, other_node,
                                weight=weight,
                                original_speed=combined_speed,
                                label=f"{combined_speed:.2f} Mbps" if combined_speed != float('inf') else "∞")

            # 5. Calcular mejores rutas usando Dijkstra
            best_routes = {}
            distances, paths = nx.single_source_dijkstra(G, origin_node)
            
            for node in G.nodes():
                if node != origin_node:
                    if node in distances:
                        # Obtener ancho de banda efectivo (mínimo en la ruta)
                        path = paths[node]
                        bandwidths = []
                        for i in range(len(path)-1):
                            u, v = path[i], path[i+1]
                            bandwidths.append(G[u][v]['original_speed'])
                        
                        effective_bandwidth = min(bandwidths) if bandwidths else 0
                    else:
                        effective_bandwidth = float('inf')

                    best_routes[node] = {
                        'ancho_banda_efectivo': effective_bandwidth,
                        'ruta': paths.get(node, []),
                        'distancia': distances.get(node, float('inf'))
                    }

            # 6. Encontrar el nodo con mejor conexión
            valid_routes = {k: v for k, v in best_routes.items() 
                        if v['distancia'] != float('inf')}
            best_dest = min(valid_routes.keys(), 
                        key=lambda x: best_routes[x]['distancia']) if valid_routes else None

            # 7. Visualización del grafo
            plt.figure(figsize=(14, 10))
            pos = nx.spring_layout(G, k=0.8, seed=42)
            
            # Configurar nodos
            node_colors = []
            node_labels = {}
            for node in G.nodes():
                if node == origin_node:
                    node_colors.append('#4CAF50')  # Verde
                    node_labels[node] = "Origen"
                elif node == best_dest:
                    node_colors.append('#F44336')  # Rojo
                    node_labels[node] = node_mapping.get(node, node)
                else:
                    node_colors.append('#2196F3')  # Azul
                    node_labels[node] = node_mapping.get(node, node)

            # Dibujar el grafo
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=800)
            nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)
            
            # Dibujar todas las conexiones
            nx.draw_networkx_edges(G, pos, alpha=0.3, edge_color='gray')
            
            # Resaltar la mejor ruta
            if best_dest:
                best_path = paths[best_dest]
                path_edges = list(zip(best_path[:-1], best_path[1:]))
                nx.draw_networkx_edges(G, pos, edgelist=path_edges,
                                    edge_color='#4CAF50', width=2.5, alpha=0.7)

            # Mostrar etiquetas de ancho de banda
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)

            # Configuración del gráfico
            plt.title(f"Topología de Red - Mejor ruta: {node_mapping.get(best_dest, 'N/A')}\n"
                    f"Ancho de banda efectivo: {best_routes.get(best_dest, {}).get('ancho_banda_efectivo', 'N/A'):.2f} Mbps",
                    fontsize=10)
            plt.tight_layout()
            
            # Guardar el gráfico
            plt.savefig(self.graph_output, dpi=300, bbox_inches='tight')
            plt.close()

            # 8. Retornar datos estructurados
            graph_data = {
                'graph': G,
                'origin_node': origin_node,
                'best_routes': best_routes,
                'best_destination': best_dest,
                'node_mapping': node_mapping,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return graph_data

        except Exception as e:
            self.log(f"\nError al generar gráfico: {str(e)}", level="error")
            messagebox.showerror("Error", f"Error al generar gráfico: {str(e)}")
            return None

    def _safe_log(self, message):
            """Método seguro para logging desde el hilo principal"""
            if not self.root.winfo_exists():  # Verificar si la ventana aún existe
                return
                
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.results_text.see(tk.END)
            self.root.update_idletasks()
    def display_graph(self):
        img = ctk.CTkImage(Image.open(self.graph_output), size=(800, 600))
        label = ctk.CTkLabel(self.graph_label, image=img, text="")
        label.pack()
    
    def clear_results(self):
        self.results_text.delete(1.0, tk.END)
        if self.graph_canvas:
            self.graph_canvas.get_tk_widget().destroy()
            self.graph_canvas = None
        self.graph_label = ttk.Label(self.root.winfo_children()[0].winfo_children()[2], 
                                   text="El gráfico aparecerá aquí después de las pruebas")
        
    
    def run_latency_test(self):
        self.clear_results()
        threading.Thread(target=self._run_latency_test, daemon=True).start()
    
    def _run_latency_test(self):
        try:
            self.log("Ejecutando prueba de latencia...\n")
            result = subprocess.run(
                ["python", self.latency_path],
                cwd=os.path.dirname(self.latency_path),
                capture_output=True,
                text=True
            )
            self.log(result.stdout)
            self.log("Prueba de latencia completada")
        except Exception as e:
            self.log(f"Error: {str(e)}")
    
    def run_bandwidth_test(self):
        self.clear_results()
        threading.Thread(target=self._run_bandwidth_test, daemon=True).start()
    
    def _run_bandwidth_test(self):
        try:
            self.log("\nEjecutando prueba de ancho de banda...")
            result = subprocess.run(
                ["python", self.bandwidth_path],
                cwd=os.path.dirname(self.bandwidth_path),
                capture_output=True,
                text=True
            )
            self.log(result.stdout)
            
            self.log("\nGenerando gráfico...")
            self.generate_network_graph()
            
            self.log("Prueba de ancho de banda completada")
        except Exception as e:
            self.log(f"Error: {str(e)}")
    
    def show_graph(self):
        if os.path.exists(self.graph_output):
            self.display_graph()
        else:
            messagebox.showwarning("Advertencia", "Primero ejecute las pruebas para generar el gráfico")
       
if __name__ == "__main__":
        root = tk.Tk()
        root.geometry("1000x800")
        
        # Centrar ventana
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        app = AlgoVPNApp(root)
        root.mainloop()