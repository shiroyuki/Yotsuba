''' Data Structures for Mathematical Graph for Yotsuba 3 '''

from time import time
from yotsuba.core import base

__scan_only__ = ['Graph', 'Vertex']
__version__ = 1.0

class Graph(list):
    ''' Data structure representing a graph. '''
    
    def get_edges_to_others(self):
        '''
        Get the list of all vertices of the other graphs that connecting to this
        graph. (Make a connected-or-not-connected subgraph from it.)
        '''
        return Graph()
    
    @staticmethod
    def is_abstract_of(obj_ref):
        '''
        Check if the object is an instance of this class.
        '''
        return type(obj_ref) is Graph

class Vertex(object):
    ''' Data structure representing a vertex in a graph. '''
    DEFAULT_EDGE_WEIGHT             = 0
    DEFAULT_MAKE_DIRECTIONAL_EDGE   = False
    
    def __init__(self, name, adjacents = None):
        '''
        Data structure representing a vertex in a graph.
        
        *name* (required, string) is the name of the vertex.
        
        *adjacents* (optional, list, default: None) is a list of neighbours (*graph.Vertex*).
        '''
        self.init(name, adjacents = None)
    
    def init(self, name, adjacents = None):
        '''
        Secondary constructor for lazy instantiation or resetting.
        
        See the constructor for the usage.
        '''
        self.name       = name
        self.adjacents  = Graph()
        self.__creation_time__ = time()
        
        if adjacents: self.adjacents.extend(adjacents)
    
    def guid(self):
        '''
        GUID of the vertex
        '''
        guid_original = "%s@%s" % (self.name, self.__creation_time__)
        return base.hash(guid_original)
    
    def make_edge_to(self, vertex):
        '''
        Make an edge to the another *vertex* (required, *graph.Vertex*-based object).
        '''
        self.adjacents.append(vertex)
    
    def is_connected_to(self, vertex):
        '''
        Check if *vertex* (required, *graph.Vertex*-based object) is connected with this node.
        '''
        return vertex in self.adjacents
    
    def __str__(self):
        return u"%s %d" % (self.name, len(self.adjacents))
    
    def __eq__(self, other):
        return 
    
    @staticmethod
    def is_abstract_of(obj_ref):
        '''
        Check if the object is an instance of this class.
        '''
        return type(obj_ref) is Vertex