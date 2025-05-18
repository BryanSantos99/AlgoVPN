import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import socket
from threading import Thread

class FileSenderFrame(ttk.LabelFrame):
    def __init__(self, parent, app_instance, *args, **kwargs):
        super().__init__(parent, text="Envío Directo via Hamachi", *args, **kwargs)
        self.app = app_instance
        self.selected_file = None
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        # Campo para IP Hamachi del destino
        ttk.Label(self, text="IP Hamachi del Destino:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_ip = ttk.Entry(self)
        self.entry_ip.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.entry_ip.insert(0, "25.")  # Prefijo común en Hamachi (ajustar según tu red)

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
        
        # Botón de envío (con hilo para no bloquear la GUI)
        self.btn_send = ttk.Button(
            self,
            text="Enviar Archivo",
            command=self.start_send_thread,
            state=tk.DISABLED
        )
        self.btn_send.grid(row=3, column=0, pady=10)

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Seleccionar archivo")
        if file_path:
            self.selected_file = file_path
            self.lbl_file.config(text=os.path.basename(file_path))
            self.btn_send['state'] = tk.NORMAL if self.entry_ip.get() else tk.DISABLED

    def start_send_thread(self):
        ip_destino = self.entry_ip.get().strip()
        if not ip_destino:
            messagebox.showwarning("Error", "Ingresa la IP Hamachi del destino")
            return
            
        Thread(target=self.send_file, args=(ip_destino,), daemon=True).start()

    def send_file(self, ip_destino):
        try:
            self.btn_send['state'] = tk.DISABLED
            self.app.log(f"\nConectando a {ip_destino} via Hamachi...")

            # Configuración del socket (TCP)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(15)  # Hamachi puede tener latencia
                s.connect((ip_destino, 55555))  # Puerto fijo para Hamachi

                # Enviar metadata (nombre y tamaño)
                filename = os.path.basename(self.selected_file)
                filesize = os.path.getsize(self.selected_file)
                s.sendall(f"{filename}|{filesize}".encode())

                # Enviar archivo por chunks
                with open(self.selected_file, 'rb') as f:
                    while True:
                        data = f.read(4096)
                        if not data:
                            break
                        s.sendall(data)

            messagebox.showinfo("Éxito", f"Archivo enviado a {ip_destino}")
            self.app.log(f"¡{filename} ({filesize/1024:.2f} KB) enviado via Hamachi!")

        except socket.timeout:
            messagebox.showerror("Error", "Timeout: Verifica la IP y conexión Hamachi")
            self.app.log("Error: ¿El receptor está ejecutando el script?")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo en el envío: {str(e)}")
            self.app.log(f"Error: {str(e)}")
        finally:
            self.btn_send['state'] = tk.NORMAL
