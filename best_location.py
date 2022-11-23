#!pip install osmnx
!pip install geopandas
import networkx as nx
#import osmnx as ox
#import geopandas as gpd
#import pandas as pd
#import numpy as np
#import shapely
#from sqlalchemy import create_engine


"""подготовка графа"""

graph = nx.read_graphml('/content/graph_vasilyevsky.graphml')
graph = nx.convert_node_labels_to_integers(graph)

print(graph.number_of_edges())

for n in graph:
  if graph.nodes[n]['is_zone'] == True:
    neighbors = list(graph.neighbors(n))
    if graph.nodes[n]['area_type'] == 'small':
      for neigh in neighbors:
        if graph[n][neigh]['time'] > 5:
          graph.remove_edge(n, neigh)
    if graph.nodes[n]['area_type'] == 'medium':
      for neigh in neighbors:
        if graph[n][neigh]['time'] > 10:
          graph.remove_edge(n, neigh)

print(graph.number_of_edges())

drop = []
for n in graph:
  neighbors = list(graph.neighbors(n))
  if len(neighbors) == 0:
    drop.append(n)
graph.remove_nodes_from(drop)

for n in graph:
  if graph.nodes[n]['is_zone'] == True:
    neighbor = graph.neighbors(n)
    sum = 0
    for neigh in neighbor:
      sum += graph.nodes[neigh]['people']
    graph.nodes[n]['people_around'] = sum

existed = []
for n in graph:
  if graph.nodes[n]['is_zone'] == False:
    graph.nodes[n]['provision_ev'] = 0
    graph.nodes[n]['provision_mf'] = 0
    graph.nodes[n]['provision_ed'] = 0
    graph.nodes[n]['provision_sp'] = 0
for n in graph:
  if graph.nodes[n]['is_zone'] == True:
    neighbor = graph.neighbors(n)
    if graph.nodes[n]['type'] == 'существующее':
      existed.append(n)
      if graph.nodes[n]['functional_type'] == 'Событийное':  
        for neigh in neighbor:
          graph.nodes[neigh]['provision_ev'] += 1
      if graph.nodes[n]['functional_type'] == 'Многофункциональное':    
        for neigh in neighbor:
          graph.nodes[neigh]['provision_mf'] += 1
      if graph.nodes[n]['functional_type'] == 'Учебное':    
        for neigh in neighbor:
          graph.nodes[neigh]['provision_ed'] += 1
      if graph.nodes[n]['functional_type'] == 'Спортивное':    
        for neigh in neighbor:
          graph.nodes[neigh]['provision_sp'] += 1

#функции для выбора оптимального пространства
def best_location_full(gr, func_type):
  max = 0
  index = -1
  sum = 0
  if func_type == 'Событийное':
    prov = 'provision_ev'
  if func_type == 'Многофункциональное':
    prov = 'provision_mf'
  if func_type == 'Учебное':
    prov = 'provision_ed'
  if func_type == 'Спортивное':
    prov = 'provision_sp'
  for n in gr:
    if gr.nodes[n]['is_zone'] == True and gr.nodes[n]['type'] == 'потенциальное' and gr.nodes[n]['people_around'] * 2 / gr.nodes[n]['area'] <= 1:
      neighbor = list(gr.neighbors(n))
      for neigh in neighbor:
        if gr.nodes[neigh][prov] == 0:
          #sum += gr.nodes[neigh]['people'] / gr[n][neigh]['time']
          sum += 1 / gr[n][neigh]['time']
      if sum > max:
        index = n
        max = sum
      sum = 0
  return max, index, prov

def best_location_full1(gr, func_type):
  max = 0
  index = -1
  sum = 0
  if func_type == 'Событийное':
    prov = 'provision_ev'
  if func_type == 'Многофункциональное':
    prov = 'provision_mf'
  if func_type == 'Учебное':
    prov = 'provision_ed'
  if func_type == 'Спортивное':
    prov = 'provision_sp'
  for n in gr:
    if gr.nodes[n]['is_zone'] == True and gr.nodes[n]['type'] == 'потенциальное':
      neighbor = list(gr.neighbors(n))
      for neigh in neighbor:
        if gr.nodes[neigh][prov] == 0:
          sum += gr.nodes[neigh]['people'] / gr[n][neigh]['time']
          #sum += 1 / gr[n][neigh]['time']
      if sum > max:
        index = n
        max = sum
      sum = 0
  return max, index, prov

#Цикл для полного обслуживания
flag = 4
order = ['Многофункциональное', 'Событийное', 'Спортивное', 'Учебное']
while True:
  for func_type in order:
    loc = best_location_full(graph, func_type)
    if loc[0] != 0:
      graph.nodes[loc[1]]['type'] = 'существующее'
      graph.nodes[loc[1]]['functional_type'] = func_type
      neighbor = graph.neighbors(loc[1])
      for neigh in neighbor:
        graph.nodes[neigh][loc[2]] += 1
    else:
      flag -= 1
  if flag == 0:
    break
  flag = 4

zones_all = 0
zones_open = 0
for n in graph:
  if graph.nodes[n]['is_zone'] == True:
    zones_all += 1
    if graph.nodes[n]['type'] == 'существующее':
      zones_open += 1
      print(graph.nodes[n])
print(zones_open, zones_all)

houses_all = 0
houses_covered = 0
houses_ev = 0
houses_sp = 0
houses_mf = 0
houses_ed = 0
for n in graph:
  if graph.nodes[n]['is_zone'] == False:
    houses_all += 1
    if graph.nodes[n]['provision_ev'] >= 1:
      houses_ev += 1
    if graph.nodes[n]['provision_sp'] >= 1:
      houses_sp += 1
    if graph.nodes[n]['provision_mf'] >= 1:
      houses_mf += 1
    if graph.nodes[n]['provision_ed'] >= 1:
      houses_ed += 1
    if graph.nodes[n]['provision_ev'] >= 1 and graph.nodes[n]['provision_mf']  >= 1 and graph.nodes[n]['provision_sp']  >= 1 and graph.nodes[n]['provision_ed']  >= 1:
      houses_covered += 1
print(f'количество многофункциональных: {houses_mf}')
print(f'количество событийных: {houses_ev}')
print(f'количество спортивных: {houses_sp}')
print(f'количество учебных: {houses_ed}')
print(f'количество полностью покрытых: {houses_covered} общее количество домов: {houses_all}')

#Локальный поиск (нельзя закрывать изначально существующие ОПМ)
i = 0
closed_func = ''
nodes = list(graph)
func = {'Многофункциональное' : 'provision_mf', 'Событийное' : 'provision_ev', 'Спортивное' : 'provision_sp', 'Учебное' : 'provision_ed'}
flag = True
ls = zones_open
clsd = [0] * len(nodes)
while i < len(nodes):
  if graph.nodes[nodes[i]]['is_zone'] == True and graph.nodes[nodes[i]]['type'] == 'существующее' and nodes[i] not in existed:
    ls -= 1
    clsd[nodes[i]] -= 1
    closed_func = graph.nodes[nodes[i]]['functional_type']
    graph.nodes[nodes[i]]['functional_type'] = ''
    graph.nodes[nodes[i]]['type'] = 'потенциальное'
    neighbors = list(graph.neighbors(nodes[i]))
    for neigh in neighbors:
      graph.nodes[neigh][func[closed_func]] -= 1
    while True:
      loc = best_location_full(graph, closed_func)
      if loc[0] != 0:
        ls += 1
        graph.nodes[loc[1]]['type'] = 'существующее'
        graph.nodes[loc[1]]['functional_type'] = closed_func
        clsd[loc[1]] += 1
        neighbor = list(graph.neighbors(loc[1]))
        for neigh in neighbor:
          graph.nodes[neigh][loc[2]] += 1  
      else:
        break
    for n in graph:
      if graph.nodes[n]['is_zone'] == True and graph.nodes[n]['type'] == 'существующее' and graph.nodes[n]['functional_type'] == closed_func and n not in existed:
        neighbors = list(graph.neighbors(n))
        for neigh in neighbors:
          if graph.nodes[neigh][func[closed_func]] == 1:
            flag = False
            break
        if flag:
          ls -= 1
          clsd[n] -= 1
          graph.nodes[n]['type'] = 'потенциальное'
          graph.nodes[n]['functional_type'] = ''
          for neigh in neighbors:
            graph.nodes[neigh][func[closed_func]] -= 1
        flag = True    
    if ls >= zones_open:
      for k in range(len(clsd)):
        if clsd[k] == -1:
          graph.nodes[k]['type'] = 'существующее'
          graph.nodes[k]['functional_type'] = closed_func
          neighbor = list(graph.neighbors(k))
          for neigh in neighbor:
            graph.nodes[neigh][func[closed_func]] += 1  
          clsd[k] = 0    
        elif clsd[k] == 1:
          graph.nodes[k]['functional_type'] = ''
          graph.nodes[k]['type'] = 'потенциальное'
          neighbors = list(graph.neighbors(k))
          for neigh in neighbors:
            graph.nodes[neigh][func[closed_func]] -= 1  
          clsd[k] = 0             
      ls = zones_open
      i += 1
    else:
      i = 0
      nodes = list(graph)
      zones_open = ls
      clsd = [0] * len(nodes)
  else:
    i += 1


#Локальный поиск (можно закрывать изначально существующие ОПМ)
i = 0
closed_func = ''
nodes = list(graph)
func = {'Многофункциональное' : 'provision_mf', 'Событийное' : 'provision_ev', 'Спортивное' : 'provision_sp', 'Учебное' : 'provision_ed'}
flag = True
ls = zones_open
clsd = [0] * len(nodes)
while i < len(nodes):
  if graph.nodes[nodes[i]]['is_zone'] == True and graph.nodes[nodes[i]]['type'] == 'существующее':
    ls -= 1
    clsd[nodes[i]] -= 1
    closed_func = graph.nodes[nodes[i]]['functional_type']
    graph.nodes[nodes[i]]['functional_type'] = ''
    graph.nodes[nodes[i]]['type'] = 'потенциальное'
    neighbors = list(graph.neighbors(nodes[i]))
    for neigh in neighbors:
      graph.nodes[neigh][func[closed_func]] -= 1
    while True:
      loc = best_location_full(graph, closed_func)
      if loc[0] != 0:
        ls += 1
        graph.nodes[loc[1]]['type'] = 'существующее'
        graph.nodes[loc[1]]['functional_type'] = closed_func
        clsd[loc[1]] += 1
        neighbor = list(graph.neighbors(loc[1]))
        for neigh in neighbor:
          graph.nodes[neigh][loc[2]] += 1  
      else:
        break
    for n in graph:
      if graph.nodes[n]['is_zone'] == True and graph.nodes[n]['type'] == 'существующее' and graph.nodes[n]['functional_type'] == closed_func:
        neighbors = list(graph.neighbors(n))
        for neigh in neighbors:
          if graph.nodes[neigh][func[closed_func]] == 1:
            flag = False
            break
        if flag:
          ls -= 1
          clsd[n] -= 1
          graph.nodes[n]['type'] = 'потенциальное'
          graph.nodes[n]['functional_type'] = ''
          for neigh in neighbors:
            graph.nodes[neigh][func[closed_func]] -= 1
        flag = True    
    if ls >= zones_open:
      for k in range(len(clsd)):
        if clsd[k] == -1:
          graph.nodes[k]['type'] = 'существующее'
          graph.nodes[k]['functional_type'] = closed_func
          neighbor = list(graph.neighbors(k))
          for neigh in neighbor:
            graph.nodes[neigh][func[closed_func]] += 1  
          clsd[k] = 0    
        elif clsd[k] == 1:
          graph.nodes[k]['functional_type'] = ''
          graph.nodes[k]['type'] = 'потенциальное'
          neighbors = list(graph.neighbors(k))
          for neigh in neighbors:
            graph.nodes[neigh][func[closed_func]] -= 1  
          clsd[k] = 0             
      ls = zones_open
      i += 1
    else:
      i = 0
      nodes = list(graph)
      zones_open = ls
      clsd = [0] * len(nodes)
  else:
    i += 1

zones_all = 0
zones_open = 0
for n in graph:
  if graph.nodes[n]['is_zone'] == True:
    zones_all += 1
    if graph.nodes[n]['type'] == 'существующее':
      zones_open += 1
      print(graph.nodes[n])
print(zones_open, zones_all)

houses_all = 0
houses_covered = 0
houses_ev = 0
houses_sp = 0
houses_mf = 0
houses_ed = 0
for n in graph:
  if graph.nodes[n]['is_zone'] == False:
    houses_all += 1
    if graph.nodes[n]['provision_ev'] >= 1:
      houses_ev += 1
    if graph.nodes[n]['provision_sp'] >= 1:
      houses_sp += 1
    if graph.nodes[n]['provision_mf'] >= 1:
      houses_mf += 1
    if graph.nodes[n]['provision_ed'] >= 1:
      houses_ed += 1
    if graph.nodes[n]['provision_ev'] >= 1 and graph.nodes[n]['provision_mf']  >= 1 and graph.nodes[n]['provision_sp']  >= 1 and graph.nodes[n]['provision_ed']  >= 1:
      houses_covered += 1
print(f'количество многофункциональных: {houses_mf}')
print(f'количество событийных: {houses_ev}')
print(f'количество спортивных: {houses_sp}')
print(f'количество учебных: {houses_ed}')
print(f'количество полностью покрытых: {houses_covered} общее количество домов: {houses_all}')

#Проверка допустимости решения, если дом помечен как обслуженный одним функц типом, то его соседом должно быть хотя бы одно ОПМ этого типа
#Если все хорошо, то ничего не выведется
flag_ed = True
flag_ev = True
flag_sp = True
flag_mf = True
for n in graph:
  if graph.nodes[n]['is_zone'] == False:
    neighbor = list(graph.neighbors(n))
    if graph.nodes[n]['provision_ed'] >= 1:
      for neigh in neighbor:
        if graph.nodes[neigh]['type'] == 'существующее' and graph.nodes[neigh]['functional_type'] == 'Учебное':
          flag_ed = False
          break
    if graph.nodes[n]['provision_ev'] >= 1:
      for neig in neighbor:
        if graph.nodes[neigh]['type'] == 'существующее' and graph.nodes[neigh]['functional_type'] == 'Событийное':
          flag_ev = False
          break
    if graph.nodes[n]['provision_sp'] >= 1:
      for neig in neighbor:
        if graph.nodes[neigh]['type'] == 'существующее' and graph.nodes[neigh]['functional_type'] == 'Спортивное':
          flag_sp = False
          break
    if graph.nodes[n]['provision_mf'] >= 1:
      for neig in neighbor:
        if graph.nodes[neigh]['type'] == 'существующее' and graph.nodes[neigh]['functional_type'] == 'Многофункциональное':
          flag_mf = False
          break
    if not (flag_ed or flag_ev or flag_sp or flag_mf):
      print(n)
    flag_ed = True
    flag_ev = True
    flag_sp = True
    flag_mf = True

