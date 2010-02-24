import os
import codecs
from xml.dom import minidom

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
    def __init__(self, name, attr = None, level = None, index = None, parentNode = None, prevNode = None, nextNode = None, reference = None):
        super(graph.Vertex, self).__init__(name)
        self.__attr         = attr          is None and {}              or attr
        self.__level        = level         is None and 0               or level
        self.__index        = index         is None and 0               or index
        self.__parentNode   = parentNode    is None and None            or parentNode
        self.__prevNode     = prevNode      is None and None            or prevNode
        self.__nextNode     = nextNode      is None and None            or nextNode
        
        # [Get adjacent vertices]
        # Set up before getting adjacent vertices
        childID = -1
        childNodeBeforeCurrentNode = None
        nodeIDs = range(self.element.childNodes) # this is still in ASC order.
        reversedNodeIDs.reverse() # now it's in DESC order.
        # Recursively get the adjacent vertices (data nodes and and child nodes)
        for nodeID in reversedNodeIDs:
            XMLNode = self.element.childNodes[nodeID]
            newNode = None
            if self.__isXMLDataNode(XMLNode):
                # Make a data node.
                newNode = DataElement(XMLNode.data)
            else:
                # Register the child node.
                childID += 1
                # Make a new DOM element.
                newNode = DOMElement.make(XMLNode, self.__level + 1, childID, self, childNodeBeforeCurrentNode)
                # If we know that there is a DOM node before this one, link this node back.
                if childNodeBeforeCurrentNode is not None:
                    childNodeBeforeCurrentNode.prev(newNode)
                # Prepare for the earlier one.
                childNodeBeforeCurrentNode = newNode
            # Make a directional connection between nodes
            self.makeEdgeTo(newNode)
    
    def __isXMLDataNode(self, XMLNode):
        return XMLNode.nodeType in (XMLNode.TEXT_NODE, XMLNode.CDATA_SECTION_NODE)
    
    @staticmethod
    def make(reference, level = None, index = None, parentNode = None, nextNode  = None):
        attr = {}
        for key in reference.attributes.keys():
            attr[key] = reference.getAttribute(key)
        return Vertex(reference.tagName, attr, level, index, None, nextNode, reference)
    
    def getName(self):
        '''
        Get the name of the element
        '''
        return self.name
    
    def setName(self, newName):
        '''
        Set the name of the element
        '''
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
        returningData = []
        maxDepth = 'maxDepth' in kwargs and (base.isNaturalNumber(maxDepth) and maxDepth - 1 or None) or None
        for adjacentNode in self.adjacents:
            if adjacentNode is DataElement:
                returningData.append(DataElement.data)
            elif adjacentNode is DOMElement and (maxDepth is None or maxDepth > 0):
                # recursively get the data from the data node.
                returningData.append(adjacentNode.data(maxDepth = maxDepth))
        return ''.join(returningData)
    
    def children(self, query = None):
        '''
        Get the children of this node.
        '''
        children = []
        # When there is no query, return all children
        if query is None:
            for adjacentNode in self.adjacents:
                if adjacentNode is not DOMElement:
                    continue
                children.append(adjacentNode)
        # Otherwise, look by the query. Set maxDepth to 1 to indicate that we are only interested in the children level.
        return query is None and self.__children or self.get(query, maxDepth = 1)
    
    def parent(self, newParentNode = None):
        if type(newParentNode) is DOMElement:
            self.__parentNode = newParentNode
        return self.__parentNode
    
    def prev(self, newPrevNode = None):
        if type(newPrevNode) is DOMElement:
            self.__prevNode = newPrevNode
        return self.__prevNode
    
    def next(self, newNextNode = None):
        if type(newNextNode) is DOMElement:
            self.__nextNode = newNextNode
        return self.__nextNode
    
    def get(self, query, **kwargs):
        '''
        Get the descendant by the query.
        '''
        # set maxDepth to 1 to indicate that we are only interested in the children level.
        parser = Kotoba(self)
        return parser.get(query, **kwargs)

class DataElement(graph.Vertex):
    def __init__(self, dataString):
        super(graph.Vertex, self).__init__("Yotsuba3.Kotoba.DataElement")
        self.data = dataString

class KotobaSourceException(Exception):
    pass

class KotobaGraphException(Exception):
    pass