import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import os
import random
import json
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

class AlgoVPNApp:
    def __init__(self, root):
        self.log_queue = queue.Queue()
        root.after(100, self.process_log_queue)
        self.root = root
        self.root.title("AlgoVPN - Monitor de Red")
        self.TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "archivos_prueba")
        # Configurar rutas según tu estructura de proyecto
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # src/vpn/
        self.server_path = os.path.join(self.base_dir, "vpn", "servidor.py")
        self.latency_path = os.path.join(self.base_dir, "vpn", "latencia.py")
        self.bandwidth_path = os.path.join(self.base_dir, "vpn", "anchoBanda.py")
        self.results_dir = os.path.join(self.base_dir, "..", "docs", "resultados")
        self.test_files_dir = os.path.join(self.base_dir, "..", "archivos_prueba")
        self.graph_output = os.path.join(self.base_dir, "..", "grafo_ancho_banda.png")
        
        # Crear directorios necesarios
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.test_files_dir, exist_ok=True)
        
        # Configuración de la interfaz
        self.setup_ui()
        
        # Variables de control
        self.server_process = None
        self.graph_canvas = None
        self.start_http_server()
    
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
            self.stop_server()  # Detener cualquier otro proceso
            self.root.quit()
                
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
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
    
    def generate_network_graph(self):
        try:
            json_path = os.path.join(self.results_dir, "resultados_ancho_banda.json")
            if not os.path.exists(json_path):
                raise FileNotFoundError("No se encontraron datos de prueba")
            
            with open(json_path, "r") as f:
                data = json.load(f)
            
            G = nx.Graph()
            for node, speed in data["datos"].items():
                G.add_node(node)
                for other_node, other_speed in data["datos"].items():
                    if node != other_node:
                        weight =  speed if speed != float('inf') else float('inf')
                        G.add_edge(node, other_node, weight=weight)
            
            with plt.ioff():
                fig = plt.figure(figsize=(8, 5))
                pos = nx.spring_layout(G)
                nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=800)
                
                labels = nx.get_edge_attributes(G, "weight")
                nx.draw_networkx_edge_labels(
                    G, pos,
                    edge_labels={k: f"{v:.2f} Mbps" if v != float('inf') else "∞" for k, v in labels.items()},
                    font_color='red'
                )
                
                plt.title(f"Topología de Red\n{data['fecha']}")
                plt.savefig(self.graph_output)
                plt.close(fig)
            
            self.display_graph()
            self.log("Gráfico generado exitosamente")
        except Exception as e:
            raise Exception(f"Error al generar gráfico: {str(e)}")
    def _safe_log(self, message):
        """Método seguro para logging desde el hilo principal"""
        if not self.root.winfo_exists():  # Verificar si la ventana aún existe
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.see(tk.END)
        self.root.update_idletasks()
    def display_graph(self):
        if os.path.exists(self.graph_output):
            if self.graph_label:
                self.graph_label.destroy()
            
            fig = plt.figure(figsize=(8, 5))
            img = plt.imread(self.graph_output)
            plt.imshow(img)
            plt.axis('off')
            
            canvas = FigureCanvasTkAgg(fig, master=self.root.winfo_children()[0].winfo_children()[2])
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.graph_canvas = canvas
    
    def clear_results(self):
        self.results_text.delete(1.0, tk.END)
        if self.graph_canvas:
            self.graph_canvas.get_tk_widget().destroy()
            self.graph_canvas = None
        self.graph_label = ttk.Label(self.root.winfo_children()[0].winfo_children()[2], 
                                   text="El gráfico aparecerá aquí después de las pruebas")
        self.graph_label.pack(expand=True)
    
    def run_latency_test(self):
        self.clear_results()
        threading.Thread(target=self._run_latency_test, daemon=True).start()
    
    def _run_latency_test(self):
        try:
            self.log("Ejecutando prueba de latencia...")
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