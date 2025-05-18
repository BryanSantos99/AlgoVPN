import requests
import time
import json
from datetime import datetime
import os

def measure_bandwidth(url, size_mb):
    try:
        start = time.time()
        downloaded = 0
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=1024):
                downloaded += len(chunk)
                if downloaded >= size_mb * 1024 * 1024:
                    break
        return (size_mb * 8) / (time.time() - start)  # Mbps
    except Exception as e:
        print(f"Error: {e}")
        return 0.0

if __name__ == "__main__":
    NODES = ["25.59.177.33","25.8.106.97"]  # Actualiza con tus IPs
    TEST_FILE = "10MB.bin"
    PORT = 8080
    results = {}
    
    for ip in NODES:
        speed = measure_bandwidth(f"http://{ip}:{PORT}/{TEST_FILE}", 10)
        if speed == 0.0:
            print(f"Error al medir el ancho de banda con {ip} de tlajomulco")
            print("No se pudo medir el ancho de banda")
            continue
        results[ip] = speed
        print(f"Ancho de banda con {ip}: {speed:.2f} Mbps")

    # Guardar resultados
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "docs", "resultados")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "resultados_ancho_banda.json"), "w") as f:
        json.dump({"fecha": str(datetime.now()), "datos": results}, f)