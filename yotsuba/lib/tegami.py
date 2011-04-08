"""
[New in Yotsuba 4.0]

**Tegami** is a module providing a base class which allows an instance of this
class or its subclass to be exported as an XML or JSON data.

.. warning::
    This module is under active development.
"""

from json import dumps as json_dumps
from re import sub
from yotsuba.core import base

class Tegami(object):
    def to_dict(self, show_only_public=True):
        ''' Convert this instance into a dictionary instance '''
        attributes = {}
        for class_item in dir(self):
            # Filter a private item out
            if show_only_public and '__' in class_item[:2]: continue
            # Filter a method or a class out
            item_type = TegamiEntityProperty.type_to_string(eval('self.%s' % class_item))
            if 'method' in item_type or 'class' in item_type: continue
            # Register a public attribute
            attributes[class_item] = TegamiEntityProperty(eval('self.%s' % class_item))
        return attributes
    
    def to_json(self, show_only_public=True):
        ''' Convert this instance into a JSON object '''
        attributes = {}
        for name, property in self.to_entity(show_only_public).iteritems():
            attributes[name] = property.to_dict()
        return json_dumps(attributes)
    
    def to_xml(self, show_only_public=True):
        ''' Convert this instance into an XML document '''
        xmldoc = [
            '<?xml version="1.0" encoding="utf-8"?><entity type="%s">'
            % TegamiEntityProperty.type_to_string(self)
        ]
        for name, property in self.to_entity(show_only_public).iteritems():
            xml_data_block = property.to_xml_data_block()
            xmldoc.append('<property name="%s" type="%s">%s</property>' % (name, xml_data_block['type'], xml_data_block['reference']))
        xmldoc.append('</entity>')
        return ''.join(xmldoc)
        

class TegamiEntityProperty(object):
    def __init__(self, reference):
        self.__reference = reference
        self.__type = type(reference)
    
    def reference(self):
        return self.__reference
    
    def type(self):
        return self.__type
    
    def to_dict(self):
        __r = self.__reference
        if self.__type not in [int, float, str, unicode, tuple, list, dict]:
            __r = base.convertToUnicode(self.__reference)
        return {
            'reference': __r,
            'type': TegamiEntityProperty.type_to_string(self.__reference)
        }
    
    def to_xml_data_block(self):
        __r = self.__reference
        if self.__type not in [int, float]:
            __r = "<![CDATA[%s]]>" % base.convertToUnicode(self.__reference)
        return {
            'reference': __r,
            'type': TegamiEntityProperty.type_to_string(self.__reference)
        }
    
    @staticmethod
    def type_to_string(reference):
        return sub("^[^']+'", "", sub("'[^']+$", "", base.convertToUnicode(type(reference))))