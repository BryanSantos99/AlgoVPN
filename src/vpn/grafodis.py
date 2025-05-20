import matplotlib.pyplot as plt
import networkx as nx
import os
import json
from datetime import datetime
import heapq

class SimpleNetworkGraph:
    def __init__(self, results_dir="resultados"):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)
    
    def dijkstra(self, grafo, inicio):
        distancias = {nodo: float('inf') for nodo in grafo}
        distancias[inicio] = 0
        cola = [(0, inicio)]
        caminos = {inicio: []}  # Para guardar los caminos
        
        while cola:
            dist_actual, nodo_actual = heapq.heappop(cola)
            for vecino, datos in grafo[nodo_actual].items():
                peso = datos.get('weight', 1)  # Usamos el peso de la arista
                distancia = dist_actual + peso
                if distancia < distancias[vecino]:
                    distancias[vecino] = distancia
                    caminos[vecino] = caminos[nodo_actual] + [(nodo_actual, vecino)]
                    heapq.heappush(cola, (distancia, vecino))
        return distancias, caminos

    def generate_network_graph(self, test_results=None, origen="Origen", destino=None):
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
            G.add_node(origen, color="#4CAF50", size=500)
            
            # Agregar nodos y conexiones
            for ip, speed in test_results.items():
                node_name = f"Nodo\n{ip.split('.')[-1]}"  # Usar solo el último octeto
                G.add_node(node_name, color="#2196F3", speed=speed)
                G.add_edge(origen, node_name, weight=1/speed if speed > 0 else float('inf'), label=f"{speed:.2f} Mbps")
            
            # 3. Aplicar Dijkstra si hay un destino especificado
            camino_mas_corto = []
            if destino:
                # Convertir el grafo nx a formato de diccionario para tu función dijkstra
                grafo_dict = {n: {} for n in G.nodes()}
                for u, v, datos in G.edges(data=True):
                    grafo_dict[u][v] = {'weight': datos['weight']}
                    grafo_dict[v][u] = {'weight': datos['weight']}
                
                # Encontrar el nodo destino completo (puede necesitar ajustes según tus nombres de nodo)
                nodo_destino = next((n for n in G.nodes() if destino in n), None)
                
                if nodo_destino:
                    distancias, caminos = self.dijkstra(grafo_dict, origen)
                    if nodo_destino in caminos:
                        camino_mas_corto = caminos[nodo_destino]
            
            # 4. Dibujar el grafo
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
            
            # Dibujar todas las conexiones
            edge_widths = [1/(G[u][v]["weight"] if G[u][v]["weight"] > 0 else 1) / 10 for u, v in G.edges()]
            all_edges = nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color="#777777", alpha=0.3)
            
            # Resaltar el camino más corto si existe
            if camino_mas_corto:
                nx.draw_networkx_edges(
                    G, pos,
                    edgelist=camino_mas_corto,
                    width=[edge_widths[list(G.edges()).index((u,v))] for u, v in camino_mas_corto],
                    edge_color='red',
                    alpha=0.7
                )
                # Dibujar nodos del camino en otro color
                nodes_in_path = set()
                for u, v in camino_mas_corto:
                    nodes_in_path.add(u)
                    nodes_in_path.add(v)
                
                nx.draw_networkx_nodes(
                    G, pos,
                    nodelist=list(nodes_in_path),
                    node_color='yellow',
                    node_size=[node_sizes[list(G.nodes()).index(n)] for n in nodes_in_path]
                )
            
            # Etiquetas de conexión (ancho de banda)
            edge_labels = nx.get_edge_attributes(G, "label")
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
            
            # Título
            titulo = "Topología de Red - Resultados de Ancho de Banda\n" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if camino_mas_corto and nodo_destino:
                titulo += f"\nCamino más corto a {nodo_destino} resaltado en rojo"
            plt.title(titulo, fontsize=10)
            
            plt.axis("off")  # Ocultar ejes
            plt.tight_layout()
            
            # 5. Guardar imagen
            graph_path = os.path.join(self.results_dir, "network_graph.png")
            plt.savefig(graph_path, dpi=150, bbox_inches="tight")
            plt.close()
            
            return {
                "graph_path": graph_path,
                "best_node": max(test_results.items(), key=lambda x: x[1])[0] if test_results else None,
                "shortest_path": camino_mas_corto if camino_mas_corto else None
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
    
    # Especificar un nodo destino (usando el último octeto de la IP)
    result = graph_maker.generate_network_graph(example_results, destino="1")
    
    if result:
        print(f"Grafo generado en: {result['graph_path']}")
        print(f"Mejor nodo: {result['best_node']}")
        if result['shortest_path']:
            print(f"Camino más corto: {result['shortest_path']}")
        
        # Abrir automáticamente (opcional)
        import webbrowser
        webbrowser.open(result['graph_path'])