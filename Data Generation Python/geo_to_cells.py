import pandas as pd
import numpy as np
from math import ceil, sqrt
import os
import csv
import datetime as dt
from copy import deepcopy
import random as rd

import osmnx as ox
import networkx as nx
from YenKShortestPaths import YenKShortestPaths

#constant values

SURFACE_AREA_CELL = 2.25
CELL_EDGE_LENGTH = 1.5
NUM_CELLS_PER_WIDTH = 2
NUM_CELLS_PER_ZONE = NUM_CELLS_PER_WIDTH * 2
MULT_FACTOR = 10000000
DISTANCE_RANGE = 100
# START_ADDRESS = '61 Boronia Street, Kensington, Sydney'
START_ADDRESS = 'Alberta St, Sydney'


MAX_ROUTES = 1
ROUTE_CONV_NAME = 'RT'

TIME_INCREMENT = 0.3
TRAVEL_TIME = 10.6

odMatrixFileName = 'D:\\UNSW\\rCITI\\OSMNX Python\\ODMatrix.txt'
FILE_CREATION_PATH = "D:\\UNSW\\rCITI\\OSMNX Python"
FILE_FORMAT = ".txt"

STRAIGHT_LENGTH = 1.5
TURN_LENGTH = 1.0607
BI_DIRECTION = 'true'

def createCells(node_list, lat_List, lon_list, node_length, node_link_list, node_coordinates):
    global NUM_CELLS_PER_ZONE
    cells_dict = {'cellName':[], 'zone':[], 'surfaceSize':[], 'coordinate':[]}
    node_serial = 1
    zone_serial = 1
    lat_min_par, long_min_par, lat_max_par, long_max_par = getNormalizeParameter(lat_list, lon_list)
    for node in node_link_list:
        tot_count = int(getCellCount(node))
        for i in range(tot_count):
            cell_Name = getCellName(str(node[0]) + str(node[1]) ,i)
            cells_dict['cellName'].append(cell_Name)
            cells_dict['zone'].append(getZoneName(str(node[0]) + str(node[1]) ,ceil(i//NUM_CELLS_PER_ZONE)))
            cells_dict['surfaceSize'].append(getSurfaceArea())
            cells_dict['coordinate'].append(getCoordinates(lat_min_par, long_min_par, node, node_coordinates, i, tot_count))
    return cells_dict

def translateLength(node):
    print(node)
    print(node_length[(node_length['u'] == node[0]) & (node_length['v'] == node[1])]["length"])
    length = list(node_length[(node_length['u'] == node[0]) & (node_length['v'] == node[1])]["length"])[0]
    global CELL_EDGE_LENGTH
    translatedLength = (length // CELL_EDGE_LENGTH) * CELL_EDGE_LENGTH
    return translatedLength

def getCellCount(node):
    global CELL_EDGE_LENGTH
    global NUM_CELLS_PER_WIDTH
    count = ((translateLength(node))//CELL_EDGE_LENGTH) * NUM_CELLS_PER_WIDTH
    return count

def getCellName(osmId, serial):
    #start with C followed by osmid and serial num C<osmnxId><serial num>
    cellName = 'C' + str(osmId) + str(serial)
    return cellName

def getZoneName(cellName, serial):
    #start Z<cellName><serial num>
    zoneName = 'Z' + cellName + str(serial)
    return zoneName

def getSurfaceArea():
    global SURFACE_AREA_CELL
    return SURFACE_AREA_CELL

def getCoordinates(lat_min, long_min, node, node_coordinates, serial_num, tot_count):
    #each block is defined as 1.5 units in length  "(-1.5|0) (0|0) (0|1.5) (-1.5|1.5)"
    lat1 = list(node_coordinates[node_coordinates['osmid']==node[0]]['x'])[0]
    lon1 = list(node_coordinates[node_coordinates['osmid']==node[0]]['y'])[0]
    lat2 = list(node_coordinates[node_coordinates['osmid']==node[1]]['x'])[0]
    lon2 = list(node_coordinates[node_coordinates['osmid']==node[1]]['y'])[0]
    length = list(node_length[(node_length['u'] == node[0]) & (node_length['v'] == node[1])]["length"])[0]
    nor_lat1, nor_lon1 = getNormalizedCoordinates(lat_min, long_min, lat1, lon1)
    nor_lat2, nor_lon2 = getNormalizedCoordinates(lat_min, long_min, lat2, lon2)
    distance = getDistance(nor_lat1, nor_lon1, nor_lat2, nor_lon2)
    if distance == 0:
        distance = 0.0000000001
    nor_lat1 = nor_lat1*(length/distance)
    nor_lon1 = nor_lon1*(length/distance)
    nor_lat2 = nor_lat2*(length/distance)
    nor_lon2 = nor_lon2*(length/distance)
    slope = getSlope(nor_lat1, nor_lon1, nor_lat2, nor_lon2)
    dx1, dy1 = getDivisionPoint((serial_num//2), nor_lat1, nor_lon1, nor_lat2, nor_lon2, ceil(tot_count/2))
    dx2, dy2 = getDivisionPoint((serial_num//2) + 1, nor_lat1, nor_lon1, nor_lat2, nor_lon2, ceil(tot_count/2))
    px1, py1 = getPerprndicularCoordinates(dx1, dy1, slope, serial_num)
    px2, py2 = getPerprndicularCoordinates(dx2, dy2, slope, serial_num)
    print(str(int(nor_lat1)) + ' ' + str(int(nor_lon1)) + ' ' + str(int(nor_lat2)) + ' ' + str(int(nor_lon2)))
    cord = '(' + str(dx1) + '|' + str(dy1) +')' + ' (' + str(px1) + '|' + str(py1) +')' + ' (' + str(px2) + '|' + str(py2) +')' + ' (' + str(dx2) + '|' + str(dy2) +')'
    print(cord)
    return cord

def getNormalizedCoordinates(lat_min, long_min, lat, lon):
    global MULT_FACTOR
    nor_lat = ((abs(lat) - abs(lat_min))*MULT_FACTOR)
    nor_lon = ((abs(lon) - abs(long_min))*MULT_FACTOR)
    return nor_lat, nor_lon

def getDistance(x1, y1, x2, y2):
    distance = sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance

def getSlope(x1, y1, x2, y2):
    slope = (y2 - y1)/(x2 - x1)
    perpendicularSlope = (1/slope)*(-1)
    return perpendicularSlope

def getNormalizeParameter(lat_List, lon_List):
    lat_min = 0
    long_min = 0
    lat_max = 0
    long_max = 0
    if lat_list[0] > 0 :
        lat_min = min(lat_List)
        lat_max = max(lat_List)
    else:
        lat_min = max(lat_List)
        lat_max = min(lat_List)
    if lon_list[0] > 0:
        long_min = min(lon_List)
        long_max = max(lon_List)
    else:
        long_min = max(lon_List) #longitudes are in -tives
        long_max = min(lon_List)
    return lat_min, long_min, lat_max, long_max

def getPerprndicularCoordinates(x1, y1, slope, serial_num):
    a = slope + 1
    b = (slope + 1)*y1*(-2)
    c = ((slope + 1)*(y1**2)) - (slope*(CELL_EDGE_LENGTH**2))
    print("a , b , c = ", a, b, c)
    print(x1, y1, slope, serial_num)
    if serial_num%2 == 0:
        y_sol = ((-1)*b + sqrt(b**2 - 4*a*c))/(2*a)
        x_sol = ((y_sol - y1)/slope) + x1
    else:
        y_sol = ((-1)*b - sqrt(b**2 - 4*a*c))/(2*a)
        x_sol = ((y_sol - y1)/slope) + x1
    return x_sol, y_sol

def getDivisionPoint(part, x1, y1, x2, y2, tot_count):
    print("part, x1, y1, x2, y2, tot_count = ", part, x1, y1, x2, y2, tot_count)
    dx = ((part*x2) + ((tot_count - part)*x1))/tot_count
    dy = ((part*y2) + ((tot_count - part)*y1))/tot_count
    print("dx, dy = ", dx, dy)
    return dx, dy


G4 = ox.graph_from_address(address=START_ADDRESS, distance=DISTANCE_RANGE, distance_type='network', network_type='walk')
graph = deepcopy(G4)

data = ox.save_load.graph_to_gdfs(G4, nodes=True, edges=True, node_geometry=False, fill_edge_geometry=False)

node_coordinates = data[0][["osmid","x","y"]]  #output is pandas framework, x is lat, y is long 
node_length = data[1][["u","v","length","oneway"]]  #output is pandas framework u and v are osmids for the nodes

lat_list = []
lon_list = []
node_list = []

node_link_list = list((G4.to_undirected()).edges())

for index, rows in node_coordinates.iterrows():
    lat_list.append(rows.x)
    lon_list.append(rows.y)
    node_list.append(int(rows.osmid))

cells_dict = createCells(node_list, lat_list, lon_list, node_length, node_link_list, node_coordinates)

cell_data = pd.DataFrame.from_dict(cells_dict)

cell_data.to_csv(os.path.join(FILE_CREATION_PATH, "new_cells_"+ str(DISTANCE_RANGE) + FILE_FORMAT), index=False)

# -------------------------- Code for generating the links -------------------------------------------------#

links_dict = {'cellName':[], 'origCellName':[], 'destCellName':[], 'length':[], 'streamOrig':[], 'streamDest':[], 'boolean bi-directional':[]}

#get the cell names while finding the routes

def createLinksData(node_list):
    print('generating links =', node_list)
    temp_list = []
    for i in range(len(node_list) -1):
        tmp1 = str(node_list[i]) + str(node_list[i+1])
        tmp2 = str(node_list[i+1]) + str(node_list[i])
        tmp = tmp1
        count = cell_data[cell_data['cellName'].str[1:len(tmp1)+1]==tmp1].zone.count()
        if count == 0:
            count = cell_data[cell_data['cellName'].str[1:len(tmp2)+1]==tmp2].zone.count()
            tmp = tmp2
        # for staright line path x-x-x 
        for j in range(count - 4):                           # ending with -2 to keep the dest within the limit of count
            links_dict['cellName'].append('C'+tmp+str(j+2))
            links_dict['origCellName'].append('C'+tmp+str(j))
            links_dict['destCellName'].append('C'+tmp+str(j+4))
            links_dict['length'].append(STRAIGHT_LENGTH)
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('E')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
        # for curving down path x-x
        #                         |
        #                         x
        for j in range(1, count - 2, 2):                           # starting with 1 since the origin is not in -ve, for odd j
            links_dict['cellName'].append('C'+tmp+str(j+2))
            links_dict['origCellName'].append('C'+tmp+str(j))
            links_dict['destCellName'].append('C'+tmp+str(j+1))
            links_dict['length'].append(TURN_LENGTH)
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('S')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
        #                       x
        #                       |
        # for curving up path x-x
        for j in range(0, count - 2, 2):                           # for even j
            links_dict['cellName'].append('C'+tmp+str(j+2))
            links_dict['origCellName'].append('C'+tmp+str(j))
            links_dict['destCellName'].append('C'+tmp+str(j+3))
            links_dict['length'].append(TURN_LENGTH)
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('N')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
        #                     x
        #                     |
        # for curving up path x-x
        for j in range(1, count - 2, 2):                           # starting with 1 since the origin is not in -ve, for odd j
            links_dict['cellName'].append('C'+tmp+str(j))
            links_dict['origCellName'].append('C'+tmp+str(j-1))
            links_dict['destCellName'].append('C'+tmp+str(j+1))
            links_dict['length'].append(TURN_LENGTH)
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('N')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
        # for curving down path x-x
        #                       |
        #                       x
        for j in range(0, count - 2, 2):                           # for even j
            links_dict['cellName'].append('C'+tmp+str(j))
            links_dict['origCellName'].append('C'+tmp+str(j+1))
            links_dict['destCellName'].append('C'+tmp+str(j+3))
            links_dict['length'].append(TURN_LENGTH)
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('S')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)

'''
        NEED TO HANDLE EDGE CASES OF ROAD INTERSECTION, START AND END POINT
'''

def createRoadIntersections(node_list):
    temp_list = []
    for i in range(len(node_list) -1):
        tmp1 = str(node_list[i]) + str(node_list[i+1])
        tmp2 = str(node_list[i+1]) + str(node_list[i])
        tmp_1 = tmp1
        count_1 = cell_data[cell_data['cellName'].str[1:len(tmp1)+1]==tmp1].zone.count()
        if count_1 == 0:
            count_1 = cell_data[cell_data['cellName'].str[1:len(tmp2)+1]==tmp2].zone.count()
            tmp_1 = tmp2
        tmp3 = str(node_list[i+1]) + str(node_list[i+2])
        tmp4 = str(node_list[i+2]) + str(node_list[i+1])
        tmp_2 = tmp3
        count_2 = cell_data[cell_data['cellName'].str[1:len(tmp3)+1]==tmp3].zone.count()
        if count_2 == 0:
            count_2 = cell_data[cell_data['cellName'].str[1:len(tmp4)+1]==tmp4].zone.count()
            tmp_2 = tmp4
        #case1-a
        links_dict['cellName'].append('C'+tmp_1+str(count_1-1))
        links_dict['origCellName'].append('C'+tmp_1+str(count_1-3))
        links_dict['destCellName'].append('C'+tmp_2+str(1))
        links_dict['length'].append(STRAIGHT_LENGTH)
        links_dict['streamOrig'].append('W')
        links_dict['streamDest'].append('E')
        links_dict['boolean bi-directional'].append(BI_DIRECTION)
        #case1-b
        links_dict['cellName'].append('C'+tmp_1+str(count_1-2))
        links_dict['origCellName'].append('C'+tmp_1+str(count_1-4))
        links_dict['destCellName'].append('C'+tmp_2+str(0))
        links_dict['length'].append(STRAIGHT_LENGTH)
        links_dict['streamOrig'].append('W')
        links_dict['streamDest'].append('E')
        links_dict['boolean bi-directional'].append(BI_DIRECTION)
        #case2
        links_dict['cellName'].append('C'+tmp_2+str(0))
        links_dict['origCellName'].append('C'+tmp_1+str(count_1-2))
        links_dict['destCellName'].append('C'+tmp_2+str(1))
        links_dict['length'].append(TURN_LENGTH)
        links_dict['streamOrig'].append('W')
        links_dict['streamDest'].append('N')
        links_dict['boolean bi-directional'].append(BI_DIRECTION)
        #case3
        links_dict['cellName'].append('C'+tmp_2+str(1))
        links_dict['origCellName'].append('C'+tmp_1+str(count_1-1))
        links_dict['destCellName'].append('C'+tmp_2+str(0))
        links_dict['length'].append(TURN_LENGTH)
        links_dict['streamOrig'].append('W')
        links_dict['streamDest'].append('S')
        links_dict['boolean bi-directional'].append(BI_DIRECTION)
        #case4
        links_dict['cellName'].append('C'+tmp_1+str(count_1-2))
        links_dict['origCellName'].append('C'+tmp_1+str(count_1-1))
        links_dict['destCellName'].append('C'+tmp_2+str(0))
        links_dict['length'].append(TURN_LENGTH)
        links_dict['streamOrig'].append('N')
        links_dict['streamDest'].append('E')
        links_dict['boolean bi-directional'].append(BI_DIRECTION)
        #case5
        links_dict['cellName'].append('C'+tmp_1+str(count_1-1))
        links_dict['origCellName'].append('C'+tmp_1+str(count_1-2))
        links_dict['destCellName'].append('C'+tmp_2+str(1))
        links_dict['length'].append(TURN_LENGTH)
        links_dict['streamOrig'].append('S')
        links_dict['streamDest'].append('E')
        links_dict['boolean bi-directional'].append(BI_DIRECTION)

def createPathEnds(node_list):
    tmp1 = str(node_list[i]) + str(node_list[i+1])
    tmp2 = str(node_list[i+1]) + str(node_list[i])
    tmp_1 = tmp1
    count_1 = cell_data[cell_data['cellName'].str[1:len(tmp1)+1]==tmp1].zone.count()
    if count_1 == 0:
        count_1 = cell_data[cell_data['cellName'].str[1:len(tmp2)+1]==tmp2].zone.count()
        tmp_1 = tmp2
    tmp3 = str(node_list[len(node_list)-1]) + str(node_list[len(node_list)-2])
    tmp4 = str(node_list[len(node_list)-2]) + str(node_list[len(node_list)-1])
    tmp_2 = tmp3
    count_2 = cell_data[cell_data['cellName'].str[1:len(tmp3)+1]==tmp3].zone.count()
    if count_2 == 0:
        count_2 = cell_data[cell_data['cellName'].str[1:len(tmp4)+1]==tmp4].zone.count()
        tmp_2 = tmp4
    #end1
    links_dict['cellName'].append('C'+tmp_2+str(count_1-1))
    links_dict['origCellName'].append('C'+tmp_2+str(count_1-3))
    links_dict['destCellName'].append('none')
    links_dict['length'].append(TURN_LENGTH)
    links_dict['streamOrig'].append('W')
    links_dict['streamDest'].append('E')
    links_dict['boolean bi-directional'].append(BI_DIRECTION)
    #end2
    links_dict['cellName'].append('C'+tmp_2+str(count_1-2))
    links_dict['origCellName'].append('C'+tmp_2+str(count_1-4))
    links_dict['destCellName'].append('none')
    links_dict['length'].append(TURN_LENGTH)
    links_dict['streamOrig'].append('W')
    links_dict['streamDest'].append('E')
    links_dict['boolean bi-directional'].append(BI_DIRECTION)
    #start1
    links_dict['cellName'].append('C'+tmp_1+str(1))
    links_dict['origCellName'].append('none')
    links_dict['destCellName'].append('C'+tmp_1+str(3))
    links_dict['length'].append(TURN_LENGTH)
    links_dict['streamOrig'].append('W')
    links_dict['streamDest'].append('E')
    links_dict['boolean bi-directional'].append(BI_DIRECTION)
    #start2
    links_dict['cellName'].append('C'+tmp_1+str(0))
    links_dict['origCellName'].append('none')
    links_dict['destCellName'].append('C'+tmp_1+str(2))
    links_dict['length'].append(TURN_LENGTH)
    links_dict['streamOrig'].append('W')
    links_dict['streamDest'].append('E')
    links_dict['boolean bi-directional'].append(BI_DIRECTION)

# -------------------------- Code for finding the routes -------------------------------------------------#

routes_data_dict = {'routeName':[],'zoneSequence':[], 'distance':[]}

def getZoneSequence(node_list):
    print('route list =', node_list)
    temp_list = []
    for i in range(len(node_list) -1):
        tmp1 = str(node_list[i]) + str(node_list[i+1])
        tmp2 = str(node_list[i+1]) + str(node_list[i])
        tmp = tmp1
        count = ceil(cell_data[cell_data['cellName'].str[1:len(tmp1)+1]==tmp1].zone.count() / 4)
        if count == 0:
            count = ceil(cell_data[cell_data['cellName'].str[1:len(tmp2)+1]==tmp2].zone.count() / 4)
            tmp = tmp2
        for j in range(count):
            temp_list.append('Z'+tmp+str(j))
    return '-'.join(str(val) for val in temp_list)

def getRouteData(orig_cord, dest_cord, serial_num):
    orig_node = ox.get_nearest_node(G4, (float(orig_cord.split('|')[0]), float(orig_cord.split('|')[1])))
    dest_node = ox.get_nearest_node(G4, (float(dest_cord.split('|')[0]), float(dest_cord.split('|')[1])))
    routes_dict = {'routeName':[],'zoneSequence':[], 'distance':[]}
    kShortestPaths = YenKShortestPaths(G4, orig_node, dest_node, 'length')
    for i in range(MAX_ROUTES):
        try:
            kShortestPathsObject = deepcopy(kShortestPaths.next())
            node_list = kShortestPathsObject.nodeList
            routes_dict['zoneSequence'].append(getZoneSequence(node_list))
            routes_dict['routeName'].append(ROUTE_CONV_NAME+str(serial_num)+str(i)) #Make changes to store muliple origin-destination pair
            routes_dict['distance'].append(kShortestPathsObject.cost)
            createLinksData(node_list)
            createRoadIntersections(node_list)
            createPathEnds(node_list)
        except:
            pass
    return routes_dict

def mergeRouteDataDict(routes_data_dict, routes_dict):
    for i in range(len(routes_dict['zoneSequence'])):
        routes_data_dict['zoneSequence'].append(routes_dict['zoneSequence'][i])
        routes_data_dict['routeName'].append(routes_dict['routeName'][i])
        routes_data_dict['distance'].append(routes_dict['distance'][i])
    return routes_data_dict


'''
route = nx.shortest_path(G4, orig_node, dest_node, weight='length')
fig, ax = ox.plot_graph_route(G4, route, node_size=0)
'''
# -------------------------- Code for generating the Demand File -------------------------------------------------#


ODMatrixList = []

demand_dict = {'routeName':[], 'depTime':[], 'numPpl':[], 'travelTime':[], 'routeName2':[],'routeName3':[]}

def getNormalizedTime(min_time, curr_time):
    temp_time = dt.datetime.strptime(curr_time, '%H:%M')
    nor_time  = (temp_time - min_time).seconds
    return nor_time

def getMinTime(ODMatrixList):
    min_time = dt.datetime.strptime('23:59:59', '%H:%M:%S') #highest possible time
    for row in ODMatrixList:
        temp_time = dt.datetime.strptime(row[2], '%H:%M')
        if min_time > temp_time:
            min_time = temp_time
    return min_time

with open(odMatrixFileName, encoding="utf8") as dataFile:
    data = csv.reader(dataFile, delimiter=',')
    for row in data:
        if '#' not in row[0]:
            ODMatrixList.append(row)

min_time = getMinTime(ODMatrixList)

serial_num = 0
for row in ODMatrixList:
    start_time = getNormalizedTime(min_time, row[2])
    demand = int(row[3])
    routes_dict = getRouteData(row[0], row[1], serial_num)
    routes_data_dict = mergeRouteDataDict(routes_data_dict, routes_dict)
    num_routes = len(routes_dict['routeName'])
    if num_routes >= 1:
    	demand_dict['routeName'].append(routes_dict['routeName'][0])
    else:
    	demand_dict['routeName'].append('NA')
    if num_routes >= 2:
	    demand_dict['routeName2'].append(routes_dict['routeName'][1])           #changes made here for testing
    else:
    	demand_dict['routeName2'].append('NA')
    if num_routes >= 3:
    	demand_dict['routeName3'].append(routes_dict['routeName'][2])
    else:
    	demand_dict['routeName3'].append('NA')
    demand_dict['numPpl'].append(str(demand))
    demand_dict['depTime'].append(str(start_time))
    demand_dict['travelTime'].append(str(TRAVEL_TIME))
    serial_num = serial_num + 1
    # rd.seed(10)
    # TIME_INCREMENT_temp = (15*60)/demand
    # if (TIME_INCREMENT_temp < TIME_INCREMENT):
    #     TIME_INCREMENT = TIME_INCREMENT_temp
    # for i in range(demand):
    #     demand_dict['routeName'].append(routes_dict['routeName'][0])
    #     demand_dict['routeName2'].append(routes_dict['routeName'][0])           #changes made here for testing
    #     demand_dict['routeName3'].append(routes_dict['routeName'][0])
    #     demand_dict['depTime'].append(str(start_time + i*rd.uniform(0,TIME_INCREMENT)))
    #     demand_dict['travelTime'].append(str(TRAVEL_TIME))

demand_data = pd.DataFrame.from_dict(demand_dict)
demand_data.to_csv(os.path.join(FILE_CREATION_PATH, "new_demand_"+ str(DISTANCE_RANGE) + FILE_FORMAT), index=False)

print('route dict =',routes_dict)


print('routes_data_dict =', routes_data_dict)
route_data = pd.DataFrame.from_dict(routes_data_dict)
route_data.to_csv(os.path.join(FILE_CREATION_PATH, "new_route_"+ str(DISTANCE_RANGE) + FILE_FORMAT), index=False)


links_data = pd.DataFrame.from_dict(links_dict)
links_data = links_data.drop_duplicates()
links_data.to_csv(os.path.join(FILE_CREATION_PATH, "new_links_"+ str(DISTANCE_RANGE) + FILE_FORMAT), index=False)
