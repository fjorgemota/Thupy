'''
Created on 05/01/2013

@author: fernando
'''
from utils import functools
from BaseUtils import BaseUtils
import logging as _logging, inspect, __builtin__
logging = _logging.getLogger("AbstractInterface")
class AbstractInterfaceType(type):
    saved = {}
    def __new__(cls, cls_name, cls_parents, cls_attrs):
        logging.info("Detectando aspectos da classe %s" % cls_name)
        logging.debug("Detectando se e uma classe abstrata ou uma interface")
        mode = map(lambda cls_parent:cls_parent.__name__, filter(lambda cls_parent: cls_parent.__name__ in ("abstract", "interface"), cls_parents))  # Detect if it's abstract or is interface
        if mode[1:]:
            mode = ["interface"]
        if not mode and cls_name in ("abstract", "interface"):
            mode = [cls_name]
        verify = False
        if not mode:
            logging.debug("Escaneando parentes para detectar um modo padrao")
            for key, classes in cls.saved.iteritems():
                if filter(lambda cls_parent: cls_parent.__name__ in classes, cls_parents):
                    verify = BaseUtils.findBases(key, cls_parents)
                    verify_mode = key
                    break
        if mode:
            logging.debug("Modo detectado: %s" % mode[0])
            cls.saved[mode[0]] = cls.saved.get(mode[0], []) + [cls_name]
            cls_attrs["__init__"] = BaseUtils.getConstructor(mode[0], cls_attrs.get("__init__"))
            cls_attrs = dict(map(BaseUtils.applyAll, cls_attrs.iteritems()))
            cls_attrs["__cls_implemented__"] = False  # Just a flag do indicate that no verified classes need to verificate in inheritance
        elif verify:
            logging.debug("Verificando como %s" % verify_mode)
            classAttrs = {}
            map(lambda child_cls: classAttrs.update(child_cls.__dict__), verify)
            classAttrs["__init__"] = classAttrs["__init__"].__oldconstructor__
            if not classAttrs["__init__"] and not cls_attrs.has_key("__init__"):
                cls_attrs["__init__"] = BaseUtils.getEmptyConstructor()
            elif not cls_attrs.has_key("__init__") and verify_mode == "abstract":
                cls_attrs["__init__"] = classAttrs["__init__"]
            cls_attrs = dict(map(BaseUtils.applyAll, cls_attrs.iteritems()))
            map(functools.partial(BaseUtils.verifyAttr, verify_mode, cls_name, classAttrs), cls_attrs.iteritems())
            methodsNotEncountered = filter(lambda attr: attr != "__metaclass__" and callable(classAttrs[attr]) and not getattr(classAttrs[attr], "__implemented__", verify_mode == "abstract") and attr not in cls_attrs, classAttrs.iterkeys())
            for method_not_encountered in methodsNotEncountered:
                raise NotImplementedError("The method '" + method_not_encountered + "' was not encountered in the class '" + cls_name + "'")
            cls.saved[verify_mode] = cls.saved.get(verify_mode, []) + [cls_name]  # Add the reference to allow the subclasses of this class to be scanned
            cls_attrs["__cls_implemented__"] = True  # Just a flag do indicate that verified classes don't need to repeat the verification in inheritance
        logging.debug("Criando classe")
        obj = super(AbstractInterfaceType, cls).__new__(cls, cls_name, cls_parents, cls_attrs)
        # Scan static attributes
        cls_static_attrs = list((attr_name, getattr(obj, attr_name)) for attr_name in dir(obj))
        # Get Only static methods
        cls_static_methods = dict((attr for attr in cls_static_attrs if callable(attr[1]) and not inspect.ismethod(attr[1]) and inspect.isfunction(attr[1])))
        map(BaseUtils.applyAll, cls_static_methods.iteritems())
        if not mode and verify:  # It's to verify?
            classStaticAttrs = {}
            map(lambda child_cls: classStaticAttrs.update(dict((attr_name, getattr(child_cls, attr_name)) for attr_name in dir(child_cls))), verify)
            # Get only static methods
            classStaticAttrs = dict((attr for attr in classStaticAttrs.iteritems() if callable(attr[1]) and not inspect.ismethod(attr[1]) and inspect.isfunction(attr[1])))
            classStaticAttrs_items = classStaticAttrs.items()
            cls_static_methods = dict((attr for attr in cls_static_methods.iteritems() if attr not in classStaticAttrs_items))
            map(functools.partial(BaseUtils.verifyAttr, verify_mode, cls_name, classStaticAttrs), cls_static_methods.iteritems())
            methodsNotEncountered = filter(lambda attr: attr != "__metaclass__" and callable(classStaticAttrs[attr]) and not getattr(classStaticAttrs[attr], "__implemented__", verify_mode == "abstract") and attr not in cls_static_methods, classStaticAttrs.iterkeys())
            for method_not_encountered in methodsNotEncountered:
                raise NotImplementedError("The static method '" + method_not_encountered + "' was not encountered in the class '" + cls_name + "'")
        # setattr(__builtin__, cls_name, obj)
        return obj
    def __repr__(self):
        cls_name = self.__name__
        cls_parents = self.__bases__
        mode = map(lambda cls_parent:cls_parent.__name__, filter(lambda cls_parent: cls_parent.__name__ in ("abstract", "interface"), cls_parents))
        if mode[1:]:
            mode = ["interface"]
        if not mode and cls_name in ("abstract", "interface"):
            mode = [cls_name]
        if not mode:
            for key, classes in AbstractInterfaceType.saved.iteritems():
                if filter(lambda cls_parent: cls_parent.__name__ in classes, cls_parents):
                    verify = BaseUtils.findBases(key, cls_parents)
                    verify_mode = key
                    break
            return "<Implementation of the %s %s with the name '%s'>" % (verify_mode, ", ".join(map(lambda cls:"'" + cls.__name__ + "'", verify)), cls_name)
        return "<%s '%s'>" % (mode[0], cls_name)
