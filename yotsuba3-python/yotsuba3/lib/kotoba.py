import os
import codecs

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
    def load(self, source):
        """
        Load the data (strictly well-formatted XML or Kotoba-compatible) from the source.
        
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
        Graph the data from XML document stored in the memory.
        """
        if self.__xmldoc is None and self.__rootElement is None:
            raise KotobaGraphException("Cannot make a (tree) graph as there is no XML document stored in the memory and there is not root element specified.")
        pass
    
    # Incomplete
    def get(self, selector):
        """
        Get the element from the selector
        """
        foundElements = []
        return foundElements
    
    # Incomplete
    def __str__(self):
        """
        Get nice presentation of the tree graph with some additional information in XML format
        """
        return '<?xml version="1.0" encoding="utf-8"?><!-- Tree Graph Representation from Kotoba --><source></source>'

class DOMElement(object):
    def __init__(self, name, attr = {}, data = '', level = 0, index = 0):
        self.name = name
        self.attr = attr
        self.data = data
        self.level = level
        self.index = index

class KotobaSourceException(Exception):
    pass

class KotobaGraphException(Exception):
    pass