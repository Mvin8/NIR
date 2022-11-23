import geopandas as gpd
import networkx as nx
import osmnx as ox
import shapely

class CreateGraph:

    def __init__(self, OPM_path, house_path):

        # iso: изохроны в формате geojson с разным временем
        # OPM: файл с потенциальными общественными пространствами
        # house: дома

        self.iso_10 = None
        self.iso_20 = None
        self.iso_5 = None
        self.OPM = gpd.read_file(OPM_path)

        house = gpd.read_file(house_path)
        h = house.to_crs(4326)
        house = h
        house['house_id'] = [15000 + i for i in range(21660)]
        self.house = house

        self.is_graph_exist = False
        self.street_graph = None
        self.graph = None


    def get_isohrone_time(self, time):
        street_graph = self.street_graph
        #buildings = gpd.read_file(objects)
        buildings = self.OPM

        def nodes_finder(street_graph, objects):
            nodes = (ox.distance.nearest_nodes(street_graph, objects.geometry.x, objects.geometry.y))
            return nodes

        def isochrones_generator_time(street_graph, obj_node, DIST):
            subgraph = nx.ego_graph(street_graph, obj_node, radius=DIST, distance="time")
            node_points = [shapely.geometry.Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
            isochrones = gpd.GeoSeries(node_points).unary_union.convex_hull
            return isochrones

        buildings_points = buildings.copy()
        buildings_points = buildings_points.to_crs(32636)
        buildings_points['geometry'] = buildings_points['geometry'].centroid
        buildings_points['node'] = nodes_finder(street_graph, buildings_points)

        buildings_iso_time = buildings_points
        buildings_iso_time.geometry = buildings_iso_time.node.apply(
            lambda x: isochrones_generator_time(street_graph, x, time))
        '''
        Необходимо построить изохроны для разных временных радиусов - 5, 10,  20,  минут.
        '''
        buildings_iso_time = buildings_iso_time.to_crs(4326)

        return buildings_iso_time


    def create_isochrones(self, path, street_graph_path = ''):
        if street_graph_path != '':
            self.street_graph = nx.read_graphml(street_graph_path)
        if path == '':
            self.iso_20 = self.get_isohrone_time(20)
            self.iso_10 = self.get_isohrone_time(10)
            self.iso_5 = self.get_isohrone_time(5)
        else:
            self.iso_20 = gpd.read_file(path + 'iso_20.geojson')
            self.iso_10 = gpd.read_file(path + 'iso_10.geojson')
            self.iso_5 = gpd.read_file(path + 'iso_5.geojson')


    def nodes_list(self, iso):
        # функция, которая возвращает словарь, где ключи - это id зон, а значения - список домов, котлорые входят в зону
        a = gpd.sjoin(iso, self.house)
        dic = {}
        for i in a.id.unique():
            dic[int(i)] = []
        for id, row in a.iterrows():
            key = row['id']
            dic[key].append(row['house_id'])

        return dic


    def add_nodes(self, isochrone, time):
        nodes = self.nodes_list(isochrone)
        for zone, value in nodes.items():
            for house in value:
                self.graph[zone][house]['time'] = time


    def create_graph(self):
        if self.is_graph_exist == False:

            nodes = self.nodes_list(self.iso_20)
            g = nx.Graph(nodes)

            for key in g.nodes():
                if key < 15000:
                    index = self.OPM[self.OPM['id'] == key].index[0]
                    g.nodes[key]['is_zone'] = True
                    g.nodes[key]['area_type'] = self.OPM.loc[index]['area_type']
                    g.nodes[key]['area'] = self.OPM.loc[index]['area']
                    g.nodes[key]['functional_type'] = self.OPM.loc[index]['functional_type']
                    g.nodes[key]['type'] = self.OPM.loc[index]['exists']
                else:
                    index = self.house[self.house['house_id'] == key].index[0]
                    g.nodes[key]['is_zone'] = False
                    g.nodes[key]['people'] = self.house.loc[index]['people']


            for zone, value in nodes.items():
                for house in value:
                    g[zone][house]['time'] = 20

            self.graph = g
            self.add_nodes(self.iso_10, 10)
            self.add_nodes(self.iso_5, 5)
            print(len(g.nodes()))

            nodes_list = g.nodes()
            for key in nodes_list:
                node = g.nodes[key]
                if node['is_zone'] == True and node['area_type'] == 'small':
                    to_remove = []
                    for house, dist in g[key].items():
                        if dist['time'] == 20:
                            to_remove.append(house)
                    for r in to_remove:
                        g.remove_edge(key, r)

            for node_id in g.nodes():
                if g.nodes[node_id]['is_zone'] == True:
                    people = 0
                    neighbours = g[node_id]
                    for key, value in neighbours.items():
                        people += g.nodes[key]['people']
                    g.nodes[node_id]['people_around'] = people

            self.is_graph_exist = True
            self.graph = g
            return self.graph

        else:
            return self.graph


