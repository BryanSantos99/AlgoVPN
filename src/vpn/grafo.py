import matplotlib.pyplot as plt
import networkx as nx
import os
import json
from datetime import datetime

class SimpleNetworkGraph:
    def __init__(self, results_dir="resultados"):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)

    def generate_network_graph(self, test_results=None):
        """Genera un grafo de red simple a partir de los resultados"""
        try:
            # 1. Obtener datos
            if test_results is None:
                json_path = os.path.join(self.results_dir, "resultados_ancho_banda.json")
                if not os.path.exists(json_path):
                    raise FileNotFoundError("No se encontraron resultados")
                
                with open(json_path, "r") as f:
                    data = json.load(f)
                test_results = data.get("datos", {})
            
            if not test_results:
                raise ValueError("No hay datos para graficar")

            # 2. Crear grafo
            G = nx.Graph()
            
            # Nodo central (origen)
            G.add_node("Origen", color="#4CAF50", size=500)
            
            # Agregar nodos y conexiones
            for ip, speed in test_results.items():
                node_name = f"Nodo\n{ip.split('.')[-1]}"  # Usar solo el último octeto
                G.add_node(node_name, color="#2196F3", speed=speed)
                G.add_edge("Origen", node_name, weight=speed, label=f"{speed:.2f} Mbps")
            
            # 3. Dibujar el grafo
            plt.figure(figsize=(10, 8))
            
            # Posiciones de los nodos (layout circular para simplicidad)
            pos = nx.circular_layout(G)
            
            # Colores y tamaños de nodos
            node_colors = [G.nodes[n]["color"] for n in G.nodes()]
            node_sizes = [G.nodes[n].get("size", 300) for n in G.nodes()]
            
            # Dibujar nodos
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
            
            # Dibujar etiquetas de nodos
            nx.draw_networkx_labels(G, pos, font_size=8)
            
            # Dibujar conexiones con grosor proporcional al ancho de banda
            edge_widths = [G[u][v]["weight"] / 10 for u, v in G.edges()]
            nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color="#777777")
            
            # Etiquetas de conexión (ancho de banda)
            edge_labels = nx.get_edge_attributes(G, "label")
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
            
            # Título
            plt.title("Topología de Red - Resultados de Ancho de Banda\n" + 
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fontsize=10)
            
            plt.axis("off")  # Ocultar ejes
            plt.tight_layout()
            
            # 4. Guardar imagen
            graph_path = os.path.join(self.results_dir, "network_graph.png")
            plt.savefig(graph_path, dpi=150, bbox_inches="tight")
            plt.close()
            
            return {
                "graph_path": graph_path,
                "best_node": max(test_results.items(), key=lambda x: x[1])[0] if test_results else None
            }

        except Exception as e:
            print(f"Error al generar grafo: {str(e)}")
            return None

# Ejemplo de uso
if __name__ == "__main__":
    # Datos de ejemplo (usar tus resultados reales)
    example_results = {
        "192.168.1.1": 45.6,
        "192.168.1.2": 32.1,
        "192.168.1.3": 28.4,
        "192.168.1.4": 12.8
    }
    
    # Generar grafo
    graph_maker = SimpleNetworkGraph()
    result = graph_maker.generate_network_graph(example_results)
    
    if result:
        print(f"Grafo generado en: {result['graph_path']}")
        print(f"Mejor nodo: {result['best_node']}")
        
        # Abrir automáticamente (opcional)
        import webbrowser
        webbrowser.open(result['graph_path'])