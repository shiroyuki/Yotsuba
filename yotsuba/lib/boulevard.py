'''
:Module: Boulevard 1.0
:Availability: Yotsuba 4.0

**Boulevard** is a wrapper to SQLAlchemy aiming to ease the setup.

.. warning::
   This module is under active development. The detail is tended to change frequently.
'''
import re
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker, clear_mappers
from sqlalchemy.exc import ArgumentError as SQLArgumentError
from sqlalchemy.exc import OperationalError as SQLOperationalError
from yotsuba.core import base as ybase

# [Exceptions]
class DataInterfaceRequired(Exception): pass
class DataInterfaceAlreadyInitialized(Exception): pass
class DataInterfaceMisconfigured(Exception): pass
class DataStoreReservedName(Exception): pass

class DataSchema(object):
    def __init__(self, kind, **attrs):
        self.__kind = kind
        self.__attrs = attrs
    
    def kind(self):
        return self.__kind
    
    def attrs(self):
        return self.__attrs

# [Data Structures]
class DataInterface(object):
    ''' Boulevard Data Interface '''
    _is_initialized = False
    schema = None
    def __init__(self, *args, **attrs):
        for k, v in attrs.iteritems():
            if k not in self.schema: continue
            try:
                self.__delattr__(k)
            except:
                pass
            self.__setattr__(k, v)

class DataStore(object):
    ''' Boulevard Data Store '''
    def __init__(self, url='sqlite:///:memory:', echo=True):
        self.engine = create_engine(url, echo=echo)
        self.metadata = MetaData(self.engine)
        self.__session = None
        self.raise_DI_init_err = False
        self.raise_DI_mapping_err = True
    
    def connect(self):
        if self.__session: return
        conn = self.engine.connect()
        SessionMaker = sessionmaker(bind=conn)
        self.__session = SessionMaker()
    
    def disconnect(self):
        if not self.__session: return
        self.__session.close()
        self.__session = None
    
    def reflect(self):
        self.metadata.create_all(self.engine)
    
    def register(self, *data_interfaces):
        ''' Register entities '''
        global __master_ctrl
        
        for data_interface in data_interfaces:
            if '_is_initialized' not in dir(data_interface):
                raise DataInterfaceRequired
            if data_interface._is_initialized and self.raise_DI_init_err:
                raise DataInterfaceAlreadyInitialized
            
            # Data Interface Name
            di_name = self.__extract_class_name(data_interface)
            
            if di_name in dir(self) and type(self.__getattribute__(di_name)) is not Table:
                raise DataStoreReservedName, "%s already in %s" % (di_name, dir(self))
            
            # Set up the data for each column
            columns = []
            for col_conf_name in data_interface.schema:
                if '_' == col_conf_name[0]: continue
                
                col_name = col_conf_name
                if len(col_name) < 1: continue
                
                col = data_interface.schema[col_conf_name]
                if type(col) is not DataSchema:
                    raise DataInterfaceMisconfigured
                
                col_conf = {
                    'type_': col.kind()
                }
                
                # Override type_
                col_conf.update(col.attrs())
                columns.append(Column(col_name, **col_conf))
            
            # Register table
            self.__setattr__(di_name, Table(di_name, self.metadata, *columns, useexisting=True))
            if not self.__getattribute__(di_name).exists():
                
                self.__getattribute__(di_name).create()
            
            # Map the schema and the interface
            try:
                mapper(data_interface, self.__getattribute__(di_name))
            except SQLArgumentError, e:
                if self.raise_DI_mapping_err:
                    raise SQLArgumentError, e
            
            # Flag as initialized
            data_interface._is_initialized = True
        # End of the loop
    
    def save(self, *data_objects):
        if len(data_objects) > 1:
            self.__session.add_all(data_objects)
        elif len(data_objects) == 1:
            self.__session.add(data_object[0])
        self.__session.commit()
    
    def find(self, data_interface):
        return self.__session.query(data_interface)
    
    def __primary_keys_of(self, di_name):
        return self.__getattribute__(di_name).primary_key.columns
    
    def __extract_class_name(self, class_ref):
        match = re.search("\.([^.]+)'>", ybase.convertToUnicode(class_ref))
        return match.groups()[0]

def clear_mappers_for_tests():
    clear_mappers()