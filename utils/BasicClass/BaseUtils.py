'''
Created on 05/01/2013

@author: fernando
'''
import inspect, logging as _logging
logging = _logging.getLogger("BaseUtils")
class BaseUtils:
    @staticmethod
    def getConstructor(mode, fn=None):
        logging.debug("Retornando construtor no modo %s"%mode)
        def constructor(*args, **kwargs):
            raise Exception("".join(["A ",mode," class cannot be constructed"]))
        constructor.__name__ = "__init__"
        constructor.__oldconstructor__ = fn
        if fn:
            logging.debug("Salvando dados do antigo construtor")
            constructor.__oldconstructor__.__arguments__ = inspect.getargspec(fn)
            constructor.__arguments__ = inspect.getargspec(fn)
        else:
            constructor.__arguments__ = inspect.getargspec(constructor)
        return constructor
    @staticmethod
    def getEmptyConstructor():
        logging.debug("Retornando construtor vazio")
        def emptyConstructor(*args, **kwargs):
            pass
        emptyConstructor.__name__ = "__init__"
        return emptyConstructor
    @staticmethod
    def verifyAttr(mode, cls_name, classAttrs, item):
        name,val = item
        if name == "__metaclass__" or ((not callable(val) and not callable(classAttrs.get(name))) or not classAttrs.get(name) or getattr(classAttrs.get(name),"__implemented__",mode=="abstract")):
            return (name, val)
        logging.debug("Verificando atributo %s da classe %s com o modo %s"%(name, cls_name, mode))
        if getattr(classAttrs.get(name),"__arguments__",None) != getattr(val,"__arguments__",None):
            raise Exception("The method '"+name+"' in the class '"+cls_name+"' has not defined correctly")
        return (name, val)
    @staticmethod
    def applyAll(item):
        name, val = item
        if name != "__metaclass__" and callable(val):
            logging.debug("Aplicando modificacoes ao metodo %s"%name)
            val.__arguments__ = inspect.getargspec(val)
        return (name,val)
    @staticmethod
    def findBases(mode, cls_parents, to = []):
        logging.debug("Procurando parentes para a classe %s"%mode)
        bases_filtered = filter(lambda child_cls: filter(lambda cls_child: cls_child.__name__ == mode, child_cls.__bases__), cls_parents)
        to.extend(bases_filtered)
        map(lambda child_cls: to.extend(BaseUtils.findBases(mode, child_cls.__bases__)), cls_parents)
        to = list(set(to))
        return to