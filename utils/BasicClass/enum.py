'''
Created on 05/01/2013

@author: fernando
'''
from utils import functools
from BaseUtils import BaseUtils
import logging as _logging, inspect
logging = _logging.getLogger("enum")
# enum
class EnumVal:
    def __init__(self, parent, name):
        self.__classname = parent
        self.__enumname = name
        EnumType.__lastCount__ += 1
        self.__value = EnumType.__lastCount__
    def __int__(self):
        return int(self.__value)

    def __repr__(self):
        return "EnumVal(%s, %s, %s)" % (self.__classname,
                                             self.__enumname,
                                             self.__value)

    def __str__(self):
        return "%s.%s" % (self.__classname, self.__enumname)

    def __cmp__(self, other):
        if not other:
            return -1 
        return cmp(str(self), str(other)) or cmp(int(self), int(other))
    def __hash__(self):
        return hash(str(self) + str(int(self)))
    def __delattr__(self, key):
        raise Exception("Cannot modify a ENUM value")
    def __setitem__(self, name, val):
        raise Exception("Cannot modify a ENUM value")
    def __delitem__(self, key):
        raise Exception("Cannot modify a ENUM value")
class EnumType(type):
    __lastCount__ = 0
    def __repr__(self):
        s = list(self.__name__)
        if self.__bases__:
            s.extend('(')
            s.extend(", ".join(map(lambda x: x.__name__,
                                          self.__bases__)))
            s.extend('):')
        if self.__dict__:
            lista = []
            for key, value in self.__dict__.iteritems():
                if key.startswith("__"):
                    continue
                lista.append(":".join([key, str(value)]))
            s.extend(", ".join(lista))
        return "".join(s)
    def __iter__(self):
        return iter(self.__dict__.values())
    def __new__(cls, cls_name, cls_parents, cls_attrs):     
        logging.info("Detectando aspectos do ENUM")
        def applyToClass(name, attrs):
            logging.debug("Escaneando classe %s" % name)
            for key, val in attrs.iteritems():
                if key.startswith("__"):
                    continue
                if inspect.isclass(val) and "enum" in val.__bases__:
                    applyToClass(".".join([name, key]), val.__dict__)
                else:
                    logging.debug("Alterando atributo %s para ENUM" % key)
                    attrs[key] = EnumVal(name, key)
            attrs["__init__"] = BaseUtils.getConstructor("enum")
            return attrs
        cls_attrs = applyToClass(cls_name, cls_attrs)
        obj = super(EnumType, cls).__new__(cls, cls_name, cls_parents, cls_attrs)
        return obj
    def getValues(self):
        return self.__dict__.values()
    def getValue(self, key):
        return getattr(self, key)
    def __setattr__(self, name, val):
        raise Exception("Cannot modify a ENUM class")
    def __delattr__(self, key):
        raise Exception("Cannot modify a ENUM class")
    def __setitem__(self, name, val):
        raise Exception("Cannot modify a ENUM class")
    def __delitem__(self, key):
        raise Exception("Cannot modify a ENUM class")
class enum(object):
    __metaclass__ = EnumType   
