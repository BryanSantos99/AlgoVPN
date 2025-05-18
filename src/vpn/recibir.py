import socket
import os
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import time

class FileReceiverWidget(ttk.LabelFrame):
    def __init__(self, parent, port=8080, save_dir=None, *args, **kwargs):
        super().__init__(parent, text="Receptor de Archivos Hamachi", *args, **kwargs)
        self.port = port
        self.save_dir = save_dir or os.path.join(os.getcwd(), "Archivos_Recibidos")
        self.server_socket = None
        self.is_running = False
        self.current_conn = None
        
        self.setup_ui()
        self.create_save_dir()
    
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        # Estado del servidor
        self.status_frame = ttk.Frame(self)
        self.status_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        ttk.Label(self.status_frame, text="Estado:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Detenido")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Información de conexión
        self.info_frame = ttk.Frame(self)
        self.info_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Label(self.info_frame, text="IP Hamachi:").pack(side=tk.LEFT)
        self.ip_var = tk.StringVar(value=self.get_hamachi_ip())
        ttk.Label(self.info_frame, textvariable=self.ip_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.info_frame, text="Puerto:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value=str(self.port))
        ttk.Label(self.info_frame, textvariable=self.port_var).pack(side=tk.LEFT)
        
        # Controles
        self.control_frame = ttk.Frame(self)
        self.control_frame.grid(row=2, column=0, pady=5)
        
        self.start_btn = ttk.Button(
            self.control_frame, 
            text="Iniciar", 
            command=self.start_server
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            self.control_frame, 
            text="Detener", 
            command=self.stop_server,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT)
        
        # Registro de actividad
        self.log_frame = ttk.LabelFrame(self, text="Registro", padding=5)
        self.log_frame.grid(row=3, column=0, sticky="nsew", pady=5)
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(self.log_frame, height=6, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Configuración de expansión
        self.grid_rowconfigure(3, weight=1)
    
    def create_save_dir(self):
        os.makedirs(self.save_dir, exist_ok=True)
        self.log(f"Archivos se guardarán en: {self.save_dir}")
    
    def get_hamachi_ip(self):
        """Obtiene automáticamente la IP de Hamachi"""
        try:
            return next(
                ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
                if ip.startswith(('25.', '5.'))
            )
        except StopIteration:
            return "No detectada"
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_server(self):
        if self.is_running:
            return
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(1)
            
            self.is_running = True
            self.status_var.set("Escuchando...")
            self.status_label.config(foreground="orange")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            Thread(target=self.accept_connections, daemon=True).start()
            self.log(f"Servidor iniciado en {self.ip_var.get()}:{self.port}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el servidor:\n{str(e)}")
            self.log(f"Error al iniciar: {str(e)}")
    
    def accept_connections(self):
        while self.is_running:
            try:
                conn, addr = self.server_socket.accept()
                self.current_conn = conn
                self.status_var.set(f"Conectado a {addr[0]}")
                self.status_label.config(foreground="green")
                self.handle_client(conn, addr)
                
            except OSError:
                break  # Socket cerrado normalmente
            except Exception as e:
                self.log(f"Error en conexión: {str(e)}")
        
        self.status_var.set("Detenido")
        self.status_label.config(foreground="red")
    
    def handle_client(self, conn, addr):
        try:
            # Recibir metadatos
            metadata = conn.recv(1024).decode().strip()
            if not metadata or '|' not in metadata:
                return
                
            filename, filesize = metadata.split('|')
            filesize = int(filesize)
            filepath = os.path.join(self.save_dir, os.path.basename(filename))
            
            self.log(f"Recibiendo: {filename} ({filesize/1024:.2f} KB)")
            
            # Recibir archivo
            received = 0
            with open(filepath, 'wb') as f:
                while received < filesize and self.is_running:
                    data = conn.recv(min(4096, filesize - received))
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
            
            if received == filesize:
                self.log(f"Transferencia completada: {filename}")
            else:
                self.log(f"Transferencia incompleta: {received}/{filesize} bytes")
                try:
                    os.remove(filepath)
                except:
                    pass
                
        except Exception as e:
            self.log(f"Error durante transferencia: {str(e)}")
        finally:
            conn.close()
            self.current_conn = None
            self.status_var.set("Escuchando...")
            self.status_label.config(foreground="orange")
    
    def stop_server(self):
        if not self.is_running:
            return
        
        self.is_running = False
        self.status_var.set("Deteniendo...")
        
        try:
            if self.current_conn:
                self.current_conn.close()
            if self.server_socket:
                self.server_socket.close()
        except:
            pass
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Servidor detenido")
    
    def set_save_directory(self, path):
        """Permite cambiar el directorio de guardado"""
        if os.path.isdir(path):
            self.save_dir = path
            self.log(f"Directorio cambiado a: {path}")
            return True
        return False

# Ejemplo de uso en una aplicación
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Aplicación con Widget Receptor")
    
    # Crear instancia del widget
    receiver = FileReceiverWidget(root, port=8080)
    receiver.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Botón de ejemplo para cambiar directorio
    def change_dir():
        new_dir = filedialog.askdirectory()
        if new_dir:
            receiver.set_save_directory(new_dir)
    
    ttk.Button(root, text="Cambiar Directorio", command=change_dir).pack(pady=5)
    
    root.mainloop()