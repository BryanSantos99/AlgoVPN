import matplotlib.pyplot as plt
import networkx as nx
import os
import json
from datetime import datetime

class SimpleNetworkGraph:
    def __init__(self, results_dir="resultados"):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)
    
    def kruskal_mst(self, grafo):
        # Convertir el grafo a lista de aristas con pesos
        edges = []
        for u in grafo:
            for v, datos in grafo[u].items():
                edges.append((u, v, datos.get('weight', 1)))
        
        # Ordenar aristas por peso
        edges.sort(key=lambda x: x[2])
        
        # Estructuras para Union-Find
        parent = {}
        rank = {}
        
        def find(node):
            if parent[node] != node:
                parent[node] = find(parent[node])
            return parent[node]
        
        def union(u, v):
            root_u = find(u)
            root_v = find(v)
            if root_u != root_v:
                if rank[root_u] > rank[root_v]:
                    parent[root_v] = root_u
                else:
                    parent[root_u] = root_v
                    if rank[root_u] == rank[root_v]:
                        rank[root_v] += 1
        
        # Inicializar estructuras
        for node in grafo:
            parent[node] = node
            rank[node] = 0
        
        mst_edges = []
        
        # Algoritmo de Kruskal
        for u, v, weight in edges:
            if find(u) != find(v):
                union(u, v)
                mst_edges.append((u, v, weight))
        
        return mst_edges

    def generate_kruskal_graph(self, test_results=None):
        """Genera un grafo mostrando solo el MST calculado con Kruskal"""
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

            # 2. Crear grafo completo
            G = nx.Graph()
            G.add_node("Origen", color="#4CAF50", size=500)
            
            for ip, speed in test_results.items():
                node_name = f"Nodo\n{ip.split('.')[-1]}"
                G.add_node(node_name, color="#2196F3", speed=speed)
                # Usamos 1/speed como peso para que conexiones más rápidas sean preferidas
                G.add_edge("Origen", node_name, 
                          weight=1/speed if speed > 0 else float('inf'),
                          original_weight=speed, 
                          label=f"{speed:.2f} Mbps")

            # 3. Calcular MST
            grafo_dict = {n: {} for n in G.nodes()}
            for u, v, datos in G.edges(data=True):
                grafo_dict[u][v] = {'weight': datos['weight']}
                grafo_dict[v][u] = {'weight': datos['weight']}
            
            mst_edges = self.kruskal_mst(grafo_dict)
            
            # 4. Crear un nuevo grafo solo con el MST
            MST = nx.Graph()
            
            # Copiar todos los nodos
            for node, data in G.nodes(data=True):
                MST.add_node(node, **data)
            
            # Agregar solo las aristas del MST
            for u, v, weight in mst_edges:
                edge_data = G.get_edge_data(u, v)
                MST.add_edge(u, v, **edge_data)
            
            # 5. Dibujar SOLO el MST
            plt.figure(figsize=(10, 8))
            pos = nx.circular_layout(MST)
            
            # Colores y tamaños de nodos
            node_colors = [MST.nodes[n]["color"] for n in MST.nodes()]
            node_sizes = [MST.nodes[n].get("size", 300) for n in MST.nodes()]
            
            # Dibujar nodos
            nx.draw_networkx_nodes(MST, pos, node_color=node_colors, node_size=node_sizes)
            
            # Dibujar etiquetas de nodos
            nx.draw_networkx_labels(MST, pos, font_size=8)
            
            # Dibujar conexiones del MST
            nx.draw_networkx_edges(
                MST, pos,
                edge_color='red',
                width=2,
                alpha=0.7
            )
            
            # Etiquetas de conexión (ancho de banda original)
            edge_labels = nx.get_edge_attributes(MST, "label")
            nx.draw_networkx_edge_labels(MST, pos, edge_labels=edge_labels, font_size=7)
            
            # Título
            plt.title("Árbol de Expansión Mínima (Kruskal)\n" + 
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fontsize=10)
            
            plt.axis("off")
            plt.tight_layout()
            
            # 6. Guardar imagen
            graph_path = os.path.join(self.results_dir, "kruskal_mst.png")
            plt.savefig(graph_path, dpi=150, bbox_inches="tight")
            plt.close()
            
            return {
                "graph_path": graph_path,
                "mst_edges": mst_edges
            }

        except Exception as e:
            print(f"Error al generar grafo: {str(e)}")
            return None

# Ejemplo de uso
if __name__ == "__main__":
    # Datos de ejemplo
    example_results = {
        "192.168.1.1": 45.6,
        "192.168.1.2": 32.1,
        "192.168.1.3": 28.4,
        "192.168.1.4": 12.8
    }
    
    # Generar grafo Kruskal
    graph_maker = SimpleNetworkGraph()
    result = graph_maker.generate_kruskal_graph(example_results)
    
    if result:
        print(f"Grafo MST generado en: {result['graph_path']}")
        print(f"Aristas del MST: {result['mst_edges']}")
        
        # Abrir automáticamente (opcional)
        import webbrowser
        webbrowser.open(result['graph_path'])