'''
Created on 17/11/2012

@author: fernando
'''
import cython, inspect, functools

#BaseUtils

class BaseUtils:
    @staticmethod
    def getConstructor(mode, fn=None):
        def constructor(*args, **kwargs):
            raise Exception("".join(["A ",mode," class cannot be constructed"]))
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
    def verifyAttr(mode, cls_name, classAttrs, item):
        name,val = item
        if name == "__metaclass__" or ((not callable(val) and not callable(classAttrs.get(name))) or not classAttrs.get(name) or getattr(classAttrs.get(name),"__implemented__",mode=="abstract")):
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
    def findBases(mode, cls_parents, to = []):
        bases_filtered = filter(lambda child_cls: filter(lambda cls_child: cls_child.__name__ == mode, child_cls.__bases__), cls_parents)
        to.extend(bases_filtered)
        map(lambda child_cls: to.extend(BaseUtils.findBases(mode, child_cls.__bases__)), cls_parents)
        to = list(set(to))
        return to
class AbstractInterfaceType(type):
    saved = {}
    @cython.locals(
              cls = object,
              cls_name=str,
              cls_parents=list,
              cls_attrs=dict)     
    def __new__(cls,cls_name, cls_parents, cls_attrs):
        mode = map(lambda cls_parent:cls_parent.__name__,filter(lambda cls_parent: cls_parent.__name__ in ("abstract","interface"),cls_parents)) #Detect if it's abstract or is interface
        if mode[1:]:
            mode = ["interface"]
        if not mode and cls_name in ("abstract","interface"):
            mode = [cls_name]
        if not mode:
            for key, classes in cls.saved.iteritems():
                if filter(lambda cls_parent: cls_parent.__name__ in classes, cls_parents):
                    verify = BaseUtils.findBases(key,cls_parents)
                    verify_mode = key
                    break
        if mode:
            print "Cadastrando como ",mode[0]
            cls.saved[mode[0]] = cls.saved.get(mode[0],[])+[cls_name]
            cls_attrs["__init__"] = BaseUtils.getConstructor(mode[0],cls_attrs.get("__init__"))
            cls_attrs = dict(map(BaseUtils.applyAll, cls_attrs.iteritems()))
        elif verify:
            print "Verificando como ",verify_mode
            classAttrs = {}
            map(lambda child_cls: classAttrs.update(child_cls.__dict__), verify)
            classAttrs["__init__"] = classAttrs["__init__"].__oldconstructor__
            if not classAttrs["__init__"] and not cls_attrs.has_key("__init__"):
                cls_attrs["__init__"] = BaseUtils.getEmptyConstructor()
            elif not cls_attrs.has_key("__init__") and verify_mode == "abstract":
                cls_attrs["__init__"] = classAttrs["__init__"]
            cls_attrs = dict(map(BaseUtils.applyAll, cls_attrs.iteritems()))
            map(functools.partial(BaseUtils.verifyAttr, verify_mode, cls_name, classAttrs), cls_attrs.iteritems())
            methodsNotEncountered = filter(lambda attr: attr!="__metaclass__" and callable(classAttrs[attr]) and not getattr(classAttrs[attr],"__implemented__",verify_mode=="abstract") and attr not in cls_attrs,classAttrs.iterkeys())
            for method_not_encountered in methodsNotEncountered:
                raise NotImplementedError("The method '"+method_not_encountered+"' was not encountered")
        obj = super(AbstractInterfaceType, cls).__new__(cls, cls_name, cls_parents, cls_attrs)
        return obj
class abstract:
    __metaclass__ = AbstractInterfaceType
def abstractFn(fn):
    fn.__implemented__ = False
    fn.__arguments__ = inspect.getargspec(fn)
    return fn

# Interface

class interface:
    __metaclass__ = AbstractInterfaceType

class CooperativeMeta(type):
    def __new__(cls, name, bases, members):
        #collect up the metaclasses
        metas = [type(base) for base in bases]

        # prune repeated or conflicting entries
        metas = [meta for index, meta in enumerate(metas)
            if not [later for later in metas[index+1:]
                if issubclass(later, meta)]]

        # whip up the actual combined meta class derive off all of these
        meta = type(name, tuple(metas), dict(combined_metas = metas))

        # make the actual object
        return meta(name, bases, members)

    def __init__(self, name, bases, members):
        for meta in self.combined_metas:
            meta.__init__(self, name, bases, members)
            
#enum
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
    def __new__(cls, cls_name, cls_parents, cls_attrs):     
        for key, val in cls_attrs.iteritems():
            if key.startswith("__"):
                continue
            cls_attrs[key] = EnumVal(cls_name, key)
        cls_attrs["__init__"] = BaseUtils.getConstructor("enum")
        obj = super(EnumType, cls).__new__(cls, cls_name, cls_parents, cls_attrs)
        return obj
    def __setattr__(self, name, val):
        raise Exception("Cannot modify a ENUM class")
    def __delattr__(self, key):
        raise Exception("Cannot modify a ENUM class")
    def __setitem__(self, name, val):
        raise Exception("Cannot modify a ENUM class")
    def __delitem__(self, key):
        raise Exception("Cannot modify a ENUM class")
class Enum:
    __metaclass__ = EnumType        
        
