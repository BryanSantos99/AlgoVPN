import subprocess
import json
from datetime import datetime
import os

def measure_latency(ip):
    try:
        result = subprocess.run(
            ["ping", "-n", "1", ip],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout
        if "TTL=" in output:
            return float(output.split("tiempo=")[1].split("ms")[0])
        return float('inf')
    except:
        return float('inf')

if __name__ == "__main__":
    NODES = ["25.59.177.33", "25.59.176.106"]  # Actualiza con tus IPs
    results = {}
    
    for ip in NODES:
        latency = measure_latency(ip)
        results[ip] = latency
        print(f"Latencia con {ip}: {latency:.2f} ms")

    # Guardar resultados
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "docs", "resultados")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "resultados_latencia.json"), "w") as f:
        json.dump({"fecha": str(datetime.now()), "datos": results}, f)