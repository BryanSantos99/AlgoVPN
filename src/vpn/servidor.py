from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import random
import sys


TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "archivos_prueba")
TEST_FILE = "10MB.bin"

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=TEST_DIR, **kwargs)

def create_test_file():
    if not os.path.exists(os.path.join(TEST_DIR, TEST_FILE)):
        os.makedirs(TEST_DIR, exist_ok=True)
        print("Creando archivo de prueba...")
        with open(os.path.join(TEST_DIR, TEST_FILE), 'wb') as f:
            f.write(random.randbytes(10 * 1024 * 1024))  # 10MB
        print("Archivo creado exitosamente")

if __name__ == "__main__":
    create_test_file()
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print(f"Servidor iniciado en http://localhost:{8000}")
    print(f"Sirviendo archivos desde: {TEST_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")