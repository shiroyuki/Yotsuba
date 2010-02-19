import os
import codecs

from yotsuba3.core import base
from yotsuba3.core import graph

class Kotoba(object):
    def __init__(self, source = None):
        """
        XML parser with CSS3 selecting specification
        """
        # Attributes
        self.__xmldoc = None
        self.__rootElement = None
        
        if source is not None:
            self.load(source)
    
    # Untested
    def read(self, source):
        """
        Read the data (strictly well-formatted XML or Kotoba-compatible) from the source.
        
        Source can be a file name, XML-formatted string or DOMElement.
        """
        # Load XML Document as a unicode file
        if source is str and os.path.exists(source):
            fp = codecs.open(source, 'r')
            self.__xmldoc = fp.read()
            fp.close()
        # XML document as string
        elif source is str and not os.path.exists(source):
            self.__xmldoc = source
        # Assign the root document with DOMElement object
        elif source is DOMElement:
            self.__rootElement = source
        # Raise exception for unknown type of source
        else:
            raise KotobaSourceException("Unknown type of source. Cannot load the data from source.")
        
        if source is str:
            self.graph()
    
    # Incomplete
    def graph(self):
        """
        Create a graph the data from XML data
        """
        if self.__xmldoc is None and self.__rootElement is None:
            raise KotobaGraphException("Cannot make a (tree) graph as there is no XML document stored in the memory and there is not root element specified.")
        pass
    
    # Incomplete
    def get(self, selector, **kargs):
        """
        Get the element from the selector
        """
        foundElements = Vertices
        return foundElements
    
    # Incomplete
    def __str__(self):
        """
        Get nice presentation of the tree graph with some additional information in XML format
        """
        return '<?xml version="1.0" encoding="utf-8"?><!-- Tree Graph Representation from Kotoba --><source></source>'

class DOMElements(graph.Graph):
    def get(self, query, **kwargs):
        elements = DOMElements()
        for vertex in self:
            parser = Kotoba(vertex)
            elements += parser.get(query, **kwargs)
        return elements
    
    def data(self):
        returningData = unicode()
        for element in self:
            returningData += element.data()
        return returningData

class DOMElement(graph.Vertex):
    def __init__(self, name, attr = None, data = None, level = None, index = None, nextNode = None, children = None, reference = None):
        super(graph.Vertex, self).__init__(name)
        self.__attr         = attr          is None and {}              or attr
        self.__data         = data          is None and unicode()       or data
        self.__level        = level         is None and 0               or level
        self.__index        = index         is None and 0               or index
        self.__parentNode   = parentNode    is None and None            or parentNode
        self.__nextNode     = nextNode      is None and None            or nextNode
        self.__children     = children      is None and DOMElements()   or children
    
    @staticmethod
    def make(reference, data = None, level = None, index = None, nextNode  = None, children = None):
        attr = {}
        for key in reference.attributes.keys():
            attr[key] = reference.getAttribute(key)
        return Vertex(reference.tagName, attr, data, level, index, nextNode, children, reference)
    
    def name(self, newName = None):
        if type(newName) is str:
            self.name = newName
        return self.name
    
    def attr(self, key, *args):
        '''
        Get the value of the given attribute. If the second parameter is given and
        its value is either number or string, this method will replace the current
        value of the attribute with whatever given. Otherwise, if it is none, the
        method will behave like deletion (self.deleteAttr).
        '''
        if len(args) > 0:
            newValue = args[0]
            if base.isString(newValue) or base.isNumber(newValue):
                # replace the value of the found attribute with `newValue`
                self.__attr[key] = newValue
            elif newValue is None and self.hasAttr(key):
                self.deleteAttr(key)
        return self.hasAttr(key) and self.__attr[key] or None
    
    def hasAttr(self, key):
        '''
        Check whether this vertex (node) has the attribute called by the given key.
        '''
        return key in self.attr
    
    def deleteAttr(self, key):
        '''
        Delete attribute if available.
        
        Returns True if succeeds.
        '''
        if self.hasAttr(key):
            return False
        del self.__attr[key]
        return True
    
    def data(self, **kwargs):
        '''
        Get data from the node.
        '''
        returningData = self.__data
        maxDepth = 'maxDepth' in kwargs and (base.isNaturalNumber(maxDepth) and maxDepth - 1 or None) or None
        if maxDepth is None or maxDepth > 0:
            for childNode in self.__children:
                # recursively get the data from the data node.
                returningData += childNode.data(maxDepth)
        return returningData
    
    def children(self, query = None):
        '''
        Get the children of this node.
        '''
        # set maxDepth to 1 to indicate that we are only interested in the children level.
        return query is None and self.__children or self.get(query, maxDepth = 1)
    
    def get(self, query, **kwargs):
        '''
        Get the descendant by the query.
        '''
        # set maxDepth to 1 to indicate that we are only interested in the children level.
        parser = Kotoba(self)
        return parser.get(query, **kwargs)

class KotobaSourceException(Exception):
    pass

class KotobaGraphException(Exception):
    pass