import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import heapq

class FileSenderFrame(ttk.LabelFrame):
    def __init__(self, parent, app_instance, *args, **kwargs):
        super().__init__(parent, text="Envío de Archivos - Selección por IP", *args, **kwargs)
        self.app = app_instance
        self.device_ips = {}  # Diccionario para mapear nombres a IPs
        self.setup_ui()
        
        
    def setup_ui(self):
        # Variables de control
        self.selected_file = None
        self.graph_data = None
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        
        # Selección de archivo
        self.file_frame = ttk.Frame(self)
        self.file_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.btn_select = ttk.Button(
            self.file_frame, 
            text="Seleccionar Archivo",
            command=self.select_file
        )
        self.btn_select.pack(side=tk.LEFT, padx=5)
        
        self.lbl_file = ttk.Label(self.file_frame, text="Ningún archivo seleccionado")
        self.lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Selección de nodo destino
        self.dest_frame = ttk.Frame(self)
        self.dest_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Label(self.dest_frame, text="Nodo Destino:").pack(side=tk.LEFT)
        
        self.cmb_dest = ttk.Combobox(self.dest_frame, state="readonly")
        self.cmb_dest.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.cmb_dest.bind("<<ComboboxSelected>>", self.update_route_info)
        
        # Información de ruta
        self.lbl_route = ttk.Label(self, text="Ruta óptima: No disponible")
        self.lbl_route.grid(row=2, column=0, sticky="w", pady=5)
        
        self.lbl_bandwidth = ttk.Label(self, text="Ancho de banda efectivo: No disponible")
        self.lbl_bandwidth.grid(row=3, column=0, sticky="w", pady=5)
        
        # Botón de envío
        self.btn_send = ttk.Button(
            self,
            text="Enviar Archivo",
            command=self.send_file,
            state=tk.DISABLED
        )
        self.btn_send.grid(row=4, column=0, pady=10)
    
    def update_graph_data(self, graph_data):
        """Actualiza los datos del grafo para envío con información de IPs"""
        self.graph_data = graph_data
        
        # Suponiendo que graph_data contiene las IPs en los datos de los nodos
        self.device_ips = {
            node: graph_data['node_info'][node].get('ip', f'IP no disponible ({node})')
            for node in graph_data['best_routes'].keys()
            if node != graph_data['origin_node']
        }
        
        # Mostrar las IPs en el combobox
        self.cmb_dest['values'] = [
            f"{ip} ({node})" if node != 'Nodo_Origen' else ip
            for node, ip in self.device_ips.items()
        ]
        
        if self.cmb_dest['values']:
            self.cmb_dest.current(0)
            self.update_route_info()
            
            
    def select_file(self):
        """Selecciona el archivo a enviar"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo para enviar",
            initialdir=os.path.expanduser("~")
        )
        
        if file_path:
            self.selected_file = file_path
            self.lbl_file.config(text=os.path.basename(file_path))
            self.btn_send['state'] = tk.NORMAL if self.cmb_dest['values'] else tk.DISABLED
    
    def update_route_info(self, event=None):
            """Actualiza la información mostrada con las IPs"""
            if not self.graph_data or not self.cmb_dest.get():
                return
                
            # Extraer el nombre del nodo de la selección (que muestra IP)
            selection = self.cmb_dest.get()
            node = selection.split('(')[-1].rstrip(')') if '(' in selection else selection
            
            route_info = self.graph_data['best_routes'].get(node, None)
            if not route_info:
                return
            
            # Formatear la ruta mostrando IPs
            formatted_route = []
            for node_in_route in route_info['ruta']:
                ip = self.graph_data['node_info'].get(node_in_route, {}).get('ip', node_in_route)
                formatted_route.append(f"{ip} ({node_in_route})")
            
            self.lbl_route.config(
                text=f"Ruta óptima: {' → '.join(formatted_route)}"
            )
            
            bandwidth = route_info['ancho_banda_efectivo']
            bw_text = (f"{bandwidth:.2f} Mbps" if bandwidth != float('inf') 
                    else "Ancho de banda ilimitado")
            self.lbl_bandwidth.config(
                text=f"Ancho de banda efectivo: {bw_text}"
            )
    
    def send_file(self):
        """Simula el envío del archivo usando la ruta óptima"""
        if not self.selected_file or not self.cmb_dest.get():
            messagebox.showwarning("Error", "Seleccione un archivo y un destino")
            return
            
        dest = self.cmb_dest.get()
        route_info = self.graph_data['best_routes'][dest]
        
        try:
            # Simulación de envío - en una implementación real aquí iría:
            # 1. La lógica para dividir el archivo en paquetes
            # 2. El envío secuencial por la ruta calculada
            # 3. Mecanismos de verificación
            
            file_name = os.path.basename(self.selected_file)
            route_str = ' → '.join(route_info['ruta'])
            bandwidth = (f"{route_info['ancho_banda_efectivo']:.2f} Mbps" 
                        if route_info['ancho_banda_efectivo'] != float('inf')
                        else "∞")
            
            msg = (
                f"Archivo: {file_name}\n"
                f"Destino: {dest}\n"
                f"Ruta óptima: {route_str}\n"
                f"Ancho de banda: {bandwidth}\n\n"
                "¡Envío simulado completado con éxito!"
            )
            
            messagebox.showinfo("Envío completado", msg)
            self.app.log(f"\nEnvío simulado: {file_name} a {dest} vía {route_str}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar archivo: {str(e)}")
            self.app.log(f"\nError en envío: {str(e)}")