import tkinter as tk
from tkinter import ttk, messagebox
from networkx import graph_atlas
import requests
import time
import json
from datetime import datetime
import os
import threading
import random
from http.server import SimpleHTTPRequestHandler, HTTPServer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import grafo

class NetworkTestWidget(ttk.Frame):
    def __init__(self, parent, nodes=None, test_size_mb=10, port=8080, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.nodes = nodes or []
        self.test_size_mb = test_size_mb
        self.port = port
        self.test_file = "10MB.bin"  # Nombre exacto del archivo
        # Ruta relativa correcta basada en tu estructura
        self.test_dir = os.path.join(os.path.dirname(__file__), "..", "archivos_prueba")
        self.server = None
        self.server_thread = None
        self.running = False
        self.test_history = []
        
        self._setup_ui()
        self._create_test_file()
    
    def _setup_ui(self):
        """Configura la interfaz completa"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Panel de control del servidor
        server_frame = ttk.LabelFrame(self, text="Control del Servidor", padding=10)
        server_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        # Botones independientes para encender/apagar
        self.btn_start_server = ttk.Button(
            server_frame, 
            text="Encender Servidor", 
            command=self._start_server,
            width=15
        )
        self.btn_start_server.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop_server = ttk.Button(
            server_frame, 
            text="Apagar Servidor", 
            command=self._stop_server,
            state=tk.DISABLED,
            width=15
        )
        self.btn_stop_server.pack(side=tk.LEFT, padx=5)
        
        self.server_status = ttk.Label(
            server_frame, 
            text="Servidor: APAGADO", 
            foreground="red"
        )
        self.server_status.pack(side=tk.LEFT, padx=10)
        
        # Panel de control de pruebas
        test_frame = ttk.LabelFrame(self, text="Pruebas de Ancho de Banda", padding=10)
        test_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        self.btn_test = ttk.Button(
            test_frame, 
            text="Iniciar Pruebas", 
            command=self._start_test,
            width=15
        )
        self.btn_test.pack(side=tk.LEFT, padx=5)
        
        self.btn_export = ttk.Button(
            test_frame, 
            text="Exportar Resultados", 
            command=self._export_results,
            state=tk.DISABLED,
            width=15
        )
        self.btn_export.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(
            test_frame, 
            orient=tk.HORIZONTAL, 
            mode='determinate'
        )
        self.progress.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        # Panel de resultados
        results_frame = ttk.LabelFrame(self, text="Resultados", padding=10)
        results_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)
        
        # Treeview para resultados
        self.results_tree = ttk.Treeview(
            results_frame, 
            columns=('node', 'speed', 'timestamp'), 
            show='headings'
        )
        self.results_tree.heading('node', text='Nodo')
        self.results_tree.heading('speed', text='Velocidad (Mbps)')
        self.results_tree.heading('timestamp', text='Fecha/Hora')
        
        scrollbar = ttk.Scrollbar(
            results_frame, 
            orient=tk.VERTICAL, 
            command=self.results_tree.yview
        )
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky="ew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Gráfico
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=results_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=2, sticky="nsew")
        self._update_chart([])
    
    def _create_test_file(self):
        """Crea el archivo de prueba si no existe"""
        os.makedirs(self.test_dir, exist_ok=True)
        file_path = os.path.join(self.test_dir, self.test_file)
        
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'wb') as f:
                    f.write(random.randbytes(self.test_size_mb * 1024 * 1024))
                self._log(f"Archivo de prueba creado: {self.test_file}")
            except Exception as e:
                self._log(f"Error creando archivo: {str(e)}", error=True)
    
    def _start_server(self):
        """Inicia el servidor HTTP"""
        try:
            self.server = HTTPServer(
                ('0.0.0.0', self.port),
                lambda *args: SimpleHTTPRequestHandler(*args, directory=self.test_dir)
            )
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            self.running = True
            
            self.server_status.config(text=f"SERVIDOR: ENCENDIDO (Puerto {self.port})", foreground="green")
            self.btn_start_server.config(state=tk.DISABLED)
            self.btn_stop_server.config(state=tk.NORMAL)
            
            self._log(f"Servidor iniciado en http://localhost:{self.port}")
            self._log(f"Archivo de prueba: {self.test_file}")
        except Exception as e:
            self._log(f"Error iniciando servidor: {str(e)}", error=True)
            messagebox.showerror("Error", f"No se pudo iniciar el servidor:\n{str(e)}")
    
    def _stop_server(self):
        """Detiene el servidor HTTP"""
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                self.running = False
                
                self.server_status.config(text="SERVIDOR: APAGADO", foreground="red")
                self.btn_start_server.config(state=tk.NORMAL)
                self.btn_stop_server.config(state=tk.DISABLED)
                
                self._log("Servidor detenido")
            except Exception as e:
                self._log(f"Error deteniendo servidor: {str(e)}", error=True)
    
    def _measure_bandwidth(self, url):
        """Mide el ancho de banda para una URL"""
        try:
            start = time.time()
            downloaded = 0
            with requests.get(url, stream=True, timeout=10) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024):
                    downloaded += len(chunk)
                    if downloaded >= self.test_size_mb * 1024 * 1024:
                        break
            return (self.test_size_mb * 8) / (time.time() - start)  # Mbps
        except Exception as e:
            self._log(f"Error midiendo ancho de banda: {str(e)}", error=True)
            return 0.0
    
    def _start_test(self):
        """Inicia las pruebas de ancho de banda"""
        if not self.nodes:
            messagebox.showwarning("Sin nodos", "No hay nodos configurados para probar")
            return
        
        # Verificar si el servidor está corriendo
        if not self.running:
            self._start_server_for_test()
        else:
            self._run_test_sequence()
    
    def _start_server_for_test(self):
        """Inicia el servidor temporalmente para las pruebas"""
        self._log("Iniciando servidor para pruebas...")
        self._start_server()
        
        # Programar las pruebas para que comiencen después de que el servidor esté listo
        self.after(1000, self._run_test_sequence)
    
    def _run_test_sequence(self):
        """Ejecuta la secuencia de pruebas"""
        self.btn_test.config(state=tk.DISABLED)
        self.progress["maximum"] = len(self.nodes)
        self.progress["value"] = 0
        
        test_thread = threading.Thread(target=self._execute_tests)
        test_thread.daemon = True
        test_thread.start()
    
    def _execute_tests(self):
        """Ejecuta las pruebas y maneja el servidor"""
        results = {}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        server_was_running = self.running
        
        try:
            for i, ip in enumerate(self.nodes, 1):
                url = f"http://{ip}:{self.port}/{self.test_file}"
                speed = self._measure_bandwidth(url)
                
                self.after(0, self._update_test_progress, i, ip, speed, timestamp)
                results[ip] = speed
                
                # Pequeña pausa entre pruebas
                time.sleep(0.5)
            
            self.after(0, self._finalize_tests, results, timestamp, server_was_running)
        except Exception as e:
            self.after(0, self._handle_test_error, e, server_was_running)
    
    def _update_test_progress(self, step, ip, speed, timestamp):
        """Actualiza la UI con los resultados parciales"""
        self.progress["value"] = step
        
        node_name = f"Nodo {ip.split('.')[-1]}"
        result_text = f"{speed:.2f} Mbps" if speed > 0 else "Error"
        
        self.results_tree.insert('', tk.END, values=(node_name, result_text, timestamp))
        self.results_tree.see(tk.END)
    
    def _finalize_tests(self, results, timestamp, keep_server_running):
        """Finaliza las pruebas y maneja el servidor"""
        self.btn_test.config(state=tk.NORMAL)
        self.btn_export.config(state=tk.NORMAL)
        
        self.test_history.append({
            "timestamp": timestamp,
            "results": results
        })
        
        self._update_chart(self.test_history)
        
        # Apagar el servidor si fue iniciado solo para las pruebas
        if not keep_server_running:
            self._stop_server()
        
        successful = sum(1 for v in results.values() if v > 0)
        messagebox.showinfo(
            "Pruebas completadas",
            f"Pruebas finalizadas:\n"
            f"Nodos probados: {len(self.nodes)}\n"
            f"Pruebas exitosas: {successful}"
        )
        graph_maker = grafo.SimpleNetworkGraph()
        graph_result = graph_maker.generate_network_graph(results)

        if graph_result:
            self._log(f"Gráfico generado: {graph_result['graph_path']}")
        
    def _handle_test_error(self, error, keep_server_running):
        """Maneja errores durante las pruebas"""
        self.btn_test.config(state=tk.NORMAL)
        messagebox.showerror("Error en pruebas", f"Ocurrió un error durante las pruebas:\n{str(error)}")
        
        # Apagar el servidor si fue iniciado solo para las pruebas
        if not keep_server_running:
            self._stop_server()
    
    def _update_chart(self, history):
        """Actualiza el gráfico con los resultados"""
        self.ax.clear()
        
        if history:
            latest = history[-1]["results"]
            nodes = [f"Nodo {ip.split('.')[-1]}" for ip in latest.keys()]
            speeds = list(latest.values())
            
            colors = ['green' if speed > 0 else 'red' for speed in speeds]
            bars = self.ax.bar(nodes, speeds, color=colors)
            
            for bar in bars:
                height = bar.get_height()
                self.ax.text(bar.get_x() + bar.get_width()/2., height,
                            f'{height:.2f}',
                            ha='center', va='bottom')
            
            self.ax.set_ylabel('Mbps')
            self.ax.set_title('Resultados de Ancho de Banda')
        else:
            self.ax.text(0.5, 0.5, 'No hay datos disponibles', 
                        ha='center', va='center')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
        
        self.canvas.draw()
    
    def _export_results(self):
        """Exporta los resultados a JSON"""
        if not self.test_history:
            messagebox.showwarning("Sin datos", "No hay resultados para exportar")
            return
            
        os.makedirs("resultados", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join("resultados", f"resultados_ancho_banda.json")
        
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "test_file": self.test_file,
                    "test_size_mb": self.test_size_mb,
                    "port": self.port,
                    "tests": self.test_history
                }, f, indent=2)
            
            messagebox.showinfo(
                "Exportación exitosa",
                f"Resultados guardados en:\n{filename}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error al exportar",
                f"No se pudieron guardar los resultados:\n{str(e)}"
            )
    
    def _log(self, message, error=False):
        """Muestra mensajes en la consola"""
        print(f"[{'ERROR' if error else 'INFO'}] {message}")
    
    def add_node(self, ip):
        """Añade un nodo a la lista de pruebas"""
        if ip not in self.nodes:
            self.nodes.append(ip)
    
    def destroy(self):
        """Asegura que el servidor se detenga al cerrar"""
        self._stop_server()
        super().destroy()


# Ejemplo de uso
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Pruebas de Red con Control de Servidor")
    root.geometry("900x700")
    
    # Nodos de ejemplo
    test_nodes = ["25.59.177.33", "25.8.106.97", "25.2.176.178"]
    
    widget = NetworkTestWidget(
        root,
        nodes=test_nodes,
        test_size_mb=10,
        port=8080
    )
    widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    root.mainloop()