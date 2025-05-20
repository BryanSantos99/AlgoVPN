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
import ancho

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
        
    
    def _safe_log(self, message):
        """Método seguro para logging desde el hilo principal"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()

    def on_closing(self):
        """Maneja el evento de cierre de la ventana"""
        if messagebox.askokcancel("Salir", "¿Está seguro que desea salir?"): 
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
            text="Mostrar Gráfico",
            command=self.show_graph
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Prueba de Latencia", 
            command=self.run_latency_test
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

        self.graph_container = ctk.CTkFrame(graph_frame)
        self.graph_container.pack(expand=True, fill=tk.BOTH)

        self.graph_text_label = ctk.CTkLabel(self.graph_container, text="El gráfico aparecerá aquí después de las pruebas")
        self.graph_text_label.pack(expand=True)

        # Añadir el frame de envío de archivos
        graph_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__),"..", "..", "resultados", "resultados_ancho_banda.json"))
        self.file_sender = FileSenderFrame(main_frame, self, graph_data=graph_data_path, padding="10")
        self.file_sender.pack(fill=tk.X, pady=10)
            # Conectar señales si es necesario
        
        # Añadir el frame de recepción de archivos
        self.file_receiver = recibir.FileReceiverWidget(main_frame)
        self.file_receiver.pack(fill=tk.X, pady=10)
        
        # Añadir el frame de envío directo
        tester = ancho.NetworkTestWidget(
            main_frame,
            nodes=["25.56.132.192", "25.8.106.97","25.59.177.33"]
        )
        tester.pack(fill=tk.BOTH, expand=True)
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
  
    def display_graph(self, image_path=None):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__),"..", ".."))
        results_dir = os.path.join(project_root, "resultados")
        image_path = os.path.join(results_dir, "network_graph.png")
        try:
            if not os.path.exists(image_path):
                messagebox.showwarning("Advertencia", "No se encontró el gráfico generado")
                return
            # Limpiar el gráfico anterior
            if hasattr(self, "graph_img_label") and self.graph_img_label:
                self.graph_img_label.destroy()
                self.graph_img_label = None
            if hasattr(self, "graph_text_label") and self.graph_text_label:
                self.graph_text_label.destroy()
                self.graph_text_label = None
            # Crear un nuevo gráfico
            Img = Image.open(image_path)
            img = ctk.CTkImage(Img, size=(400, 300))
            self.graph_img_label = ctk.CTkLabel(self.graph_container, image=img, text="")
            self.graph_img_label.image = img  # Guardar referencia
            self.graph_img_label.pack(expand=True)
        except Exception as e:
            print(f"Error al mostrar gráfico: {e}")
            
    def clear_results(self):
        self.results_text.delete(1.0, tk.END)
        if self.graph_canvas:
            self.graph_canvas.get_tk_widget().destroy()
            self.graph_canvas = None
        self.graph_label = ttk.Label(self.root.winfo_children()[0].winfo_children()[2],text="El gráfico aparecerá aquí después de las pruebas") 
    
    def run_latency_test(self):
        self.clear_results()
        threading.Thread(target=self._run_latency_test, daemon=True).start()
    
    def _run_latency_test(self):
        try:
            self.log("Ejecutando prueba de latencia... ")
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
    
    def show_graph(self):
            self.display_graph()
            
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