import tkinter as tk
from tkinter import filedialog
from algorithms.dijkstra import dijkstra

class VPN_GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Optimizador de VPN")
        self.root.geometry("400x300")
        
        # Widgets
        tk.Label(self.root, text="Seleccionar archivo:").pack()
        tk.Button(self.root, text="Examinar", command=self.seleccionar_archivo).pack()
        tk.Label(self.root, text="Nodo destino:").pack()
        self.destino = tk.Entry(self.root)
        self.destino.pack()
        tk.Button(self.root, text="Transferir", command=self.transferir).pack()
        
    def seleccionar_archivo(self):
        filedialog.askopenfilename(title="Elige un archivo")
        
    def transferir(self):
        grafo = {"nodo1": {"nodo2": 5.2}, "nodo2": {"nodo1": 5.2}}  # Ejemplo
        ruta_optima = dijkstra(grafo, "nodo1")
        print("Ruta óptima:", ruta_optima)

if __name__ == "__main__":
    app = VPN_GUI()
    app.root.mainloop()