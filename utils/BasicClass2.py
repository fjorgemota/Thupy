'''
Created on 17/11/2012

@author: fernando
'''
import cython, inspect, functools
class abstractClass(type):
    cython.locals(
              cls = object,
              cls_name=str,
              cls_parents=list,
              cls_attrs=dict)
    @staticmethod
    def getConstructor(fn):
        def constructor(*args, **kwargs):
            raise Exception("A abstract class cannot be constructed")
        constructor.__name__ = "__init__"
        constructor.__oldconstructor__ = fn
        constructor.__arguments__ = inspect.getargspec(fn or constructor)
        return constructor
    @staticmethod
    def getEmptyConstructor():
        def emptyConstructor(*args, **kwargs):
            pass
        emptyConstructor.__name__ = "__init__"
        return emptyConstructor
    @staticmethod
    def verifyAttr(cls_name, classAttrs, item):
        name,val = item
        if name == "__metaclass__" or ((not callable(val) and not callable(classAttrs.get(name))) or not classAttrs.get(name) or getattr(classAttrs.get(name),"__implemented__",True)):
            return (name, val)
        if getattr(classAttrs.get(name),"__arguments__",None) != getattr(val,"__arguments__",None):
            raise Exception("The method '"+name+"' in the class '"+cls_name+"' has not defined correctly")
        return (name, val)
    @staticmethod
    def applyAll(item):
        name, val = item
        if name != "__metaclass__" and callable(val):
            val.__arguments__ = inspect.getargspec(val)
        return (name,val)
    @staticmethod
    def findBases(cls_parents, to = []):
        bases_filtered = filter(lambda child_cls: filter(lambda cls_child: cls_child.__name__ == "abstract", child_cls.__bases__), cls_parents)
        to.extend(bases_filtered)
        map(lambda child_cls: to.extend(abstractClass.findBases(child_cls.__bases__)), cls_parents)
        to = list(set(to))
        return to
    def __new__(cls,cls_name, cls_parents, cls_attrs):
        is_inherit = filter(lambda cls_parent: cls_parent.__name__ == "abstract",cls_parents) #Apply abstract to constructor
        #verify = filter(lambda child_cls: filter(lambda cls_child: cls_child.__name__ == "abstract", child_cls.__bases__), cls_parents) #
        verify = abstractClass.findBases(cls_parents)
        if is_inherit:
            cls_attrs["__init__"] = abstractClass.getConstructor(cls_attrs.get("__init__"))
            cls_attrs = dict(map(abstractClass.applyAll, cls_attrs.iteritems()))
        elif verify:
            classAttrs = {}
            map(lambda child_cls: classAttrs.update(child_cls.__dict__), verify)
            classAttrs["__init__"] = classAttrs["__init__"].__oldconstructor__
            if not classAttrs["__init__"] and not cls_attrs.has_key("__init__"):
                cls_attrs["__init__"] = abstractClass.getEmptyConstructor()
            elif not cls_attrs.has_key("__init__"):
                cls_attrs["__init__"] = classAttrs["__init__"]
            cls_attrs = dict(map(abstractClass.applyAll, cls_attrs.iteritems()))
            map(functools.partial(abstractClass.verifyAttr, cls_name, classAttrs), cls_attrs.iteritems())
            methodsNotEncountered = filter(lambda attr: attr!="__metaclass__" and callable(classAttrs[attr]) and not getattr(classAttrs[attr],"__implemented__",True) and attr not in cls_attrs,classAttrs.iterkeys())
            for method_not_encountered in methodsNotEncountered:
                raise NotImplementedError("The method '"+method_not_encountered+"' was not encountered")
        obj = super(abstractClass, cls).__new__(cls, cls_name, cls_parents, cls_attrs)
        return obj
class abstract:
    __metaclass__ = abstractClass
def abstractFn(fn):
    fn.__implemented__ = False
    fn.__arguments__ = inspect.getargspec(fn)
    return fn

# Interface

class interfaceClass(type):
    cython.locals(
              cls = object,
              cls_name=str,
              cls_parents=list,
              cls_attrs=dict)
    @staticmethod
    def getConstructor(fn):
        def constructor(*args, **kwargs):
            raise Exception("A abstract class cannot be constructed")
        constructor.__name__ = "__init__"
        constructor.__oldconstructor__ = fn
        if fn:
            constructor.__oldconstructor__.__arguments__ = inspect.getargspec(fn)
            constructor.__arguments__ = inspect.getargspec(fn)
        else:
            constructor.__arguments__ = inspect.getargspec(constructor)
        return constructor
    @staticmethod
    def getEmptyConstructor():
        def emptyConstructor(*args, **kwargs):
            pass
        emptyConstructor.__name__ = "__init__"
        return emptyConstructor
    @staticmethod
    def verifyAttr(cls_name, classAttrs, item):
        name,val = item
        if name == "__metaclass__" or ((not callable(val) and not callable(classAttrs.get(name))) or not classAttrs.get(name)):
            return (name, val)
        if getattr(classAttrs.get(name),"__arguments__",None) != getattr(val,"__arguments__",None):
            raise Exception("The method '"+name+"' in the class '"+cls_name+"' has not defined correctly")
        return (name, val)
    @staticmethod
    def applyAll(item):
        name, val = item
        if name != "__metaclass__" and callable(val):
            val.__arguments__ = inspect.getargspec(val)
        return (name,val)
    @staticmethod
    def findBases(cls_parents, to = []):
        bases_filtered = filter(lambda child_cls: filter(lambda cls_child: cls_child.__name__ == "interface", child_cls.__bases__), cls_parents)
        to.extend(bases_filtered)
        map(lambda child_cls: to.extend(abstractClass.findBases(child_cls.__bases__)), cls_parents)
        to = list(set(to))
        return to
    def __new__(cls,cls_name, cls_parents, cls_attrs):
        is_inherit = filter(lambda cls_parent: cls_parent.__name__ == "interface",cls_parents) #Apply abstract to constructor
        #verify = filter(lambda child_cls: filter(lambda cls_child: cls_child.__name__ == "interface", child_cls.__bases__), cls_parents) #
        verify = interfaceClass.findBases(cls_parents)
        if is_inherit:
            cls_attrs["__init__"] = interfaceClass.getConstructor(cls_attrs.get("__init__"))
            cls_attrs = dict(map(interfaceClass.applyAll, cls_attrs.iteritems()))
        elif verify:
            classAttrs = {}
            map(lambda child_cls: classAttrs.update(child_cls.__dict__), verify)
            classAttrs["__init__"] = classAttrs["__init__"].__oldconstructor__
            if not classAttrs["__init__"] and not cls_attrs.has_key("__init__"):
                cls_attrs["__init__"] = interfaceClass.getEmptyConstructor()
            cls_attrs = dict(map(interfaceClass.applyAll, cls_attrs.iteritems()))
            map(functools.partial(interfaceClass.verifyAttr, cls_name, classAttrs), cls_attrs.iteritems())
            methodsNotEncountered = filter(lambda attr: attr!="__metaclass__" and callable(classAttrs[attr]) and attr not in cls_attrs,classAttrs.iterkeys())
            for method_not_encountered in methodsNotEncountered:
                raise NotImplementedError("The method '"+method_not_encountered+"' was not encountered in the class '"+cls_name+"'")
        obj = super(interfaceClass, cls).__new__(cls, cls_name, cls_parents, cls_attrs)
        return obj
class interface:
    __metaclass__ = interfaceClass
    
        