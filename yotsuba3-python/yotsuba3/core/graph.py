'''
Mathematical Graph
'''

class Graph(list):
    '''
    Mathematical graph containing vertices.
    '''
    def getConnectionsToOtherGraphs(self):
        '''
        Get the list of all vertices of the other graphs that connecting to this
        graph. (Make a connected-or-not-connected subgraph from it.)
        '''
        return Graph()
    
    @staticmethod
    def isInstance(objRef):
        return type(objRef) is Graph

class Vertex(object):
    DEFAULT_EDGE_WEIGHT             = 0
    DEFAULT_MAKE_DIRECTIONAL_EDGE   = False
    
    def __init__(self, name, adjacents = None):
        self.name       = name
        self.adjacents  = adjacents
        if self.adjacents is None:
            self.adjacents = Graph()
    
    def makeEdgeTo(self, vertex):
        self.adjacents.append(vertex)
    
    def isConnectedTo(self, otherVertex):
        return otherVertex in self.adjacents
    
    def __str__(self):
        return u"%s %d" % (self.name, len(self.adjacents))
    
    @staticmethod
    def isInstance(objRef):
        return type(objRef) is Vertex