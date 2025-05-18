import networkx as nx
import matplotlib.pyplot as plt
import json

def generar_grafo(ru):
    with open(ru, "r") as f:
        datos = json.load(f)

    G = nx.Graph()
    for nodo, velocidad in datos["datos"].items():
        G.add_node(nodo)
        # Añadir aristas (ejemplo: conexión entre nodos)
        for otro_nodo, otra_velocidad in datos["datos"].items():
            if nodo != otro_nodo:
                G.add_edge(nodo, otro_nodo, weight=1/velocidad if velocidad > 0 else float('inf'))

    # Dibujar grafo
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color="lightblue")
    etiquetas = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels={k: f"{1/v:.2f}" for k, v in etiquetas.items()})
    plt.title(f"Grafo de Ancho de Banda (Actualizado: {datos['fecha']})")
    plt.savefig("grafo_ancho_banda.png")
    plt.show()

if __name__ == "__main__":
    generar_grafo()