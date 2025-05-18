def kruskal(grafo):
    aristas = []
    for nodo in grafo:
        for vecino, peso in grafo[nodo].items():
            aristas.append((peso, nodo, vecino))
    aristas.sort()
    mst = []
    padre = {nodo: nodo for nodo in grafo}

    def encontrar_padre(nodo):
        if padre[nodo] != nodo:
            padre[nodo] = encontrar_padre(padre[nodo])
        return padre[nodo]

    for peso, u, v in aristas:
        padre_u = encontrar_padre(u)
        padre_v = encontrar_padre(v)
        if padre_u != padre_v:
            mst.append((u, v, peso))
            padre[padre_v] = padre_u
    return mst