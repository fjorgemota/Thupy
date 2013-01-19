'''
Created on 05/01/2013

@author: fernando
'''
import inspect, logging as _logging
logging = _logging.getLogger("BaseUtils")
class BaseUtils:
    @staticmethod
    def getConstructor(mode, fn=None):
        logging.debug("Retornando construtor no modo %s" % mode)
        def constructor(*args, **kwargs):
            raise Exception("".join(["A ", mode, " class cannot be constructed"]))
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
        name, val = item
        if name == "__metaclass__" or ((not callable(val) and not callable(classAttrs.get(name))) or not classAttrs.get(name) or getattr(classAttrs.get(name), "__implemented__", mode == "abstract")):
            return (name, val)
        logging.debug("Verificando atributo %s da classe %s com o modo %s" % (name, cls_name, mode))
        if getattr(classAttrs.get(name), "__arguments__", None) != getattr(val, "__arguments__", None):
            raise Exception("The method '" + name + "' in the class '" + cls_name + "' has not defined correctly (in arguments) (or it can be static..)")
        elif getattr(classAttrs.get(name), "__decorators__", []) != getattr(val, "__decorators__", []):
            raise Exception("The method '" + name + "' in the class '" + cls_name + "' don't have the correct decorators")
        return (name, val)
    @staticmethod
    def applyAll(item):
        name, val = item
        if name != "__metaclass__" and callable(val):
            logging.debug("Aplicando modificacoes ao metodo %s" % name)
            val.__arguments__ = inspect.getargspec(val)  # Save the arguments of the function
            val.__decorators__ = BaseUtils.getDecoratorHistory(val, False)  # Detect if static
            if val.__decorators__:
                val.__decorators__.pop()
        return (name, val)
    @staticmethod
    def findBases(mode, cls_parents):
        logging.debug("Procurando parentes para a classe %s" % mode)
        to = []
        bases_filtered = filter(lambda child_cls: filter(lambda cls_child: cls_child.__name__ == mode, child_cls.__bases__), cls_parents)
        to.extend(bases_filtered)
        map(lambda child_cls: to.extend(BaseUtils.findBases(mode, child_cls.__bases__)), filter(lambda child_cls: getattr(child_cls, "__cls_implemented__", True), to))
        to = list(set(to))
        logging.debug("Parentes encontrados: %s" % ", ".join(map(lambda cls: cls.__name__, to)))
        return to
    @staticmethod
    def getDecoratorHistory(fn, natural_order=False, to=[]):
        # Investigate func closures
        if not hasattr(fn, "func_closure"):
            if isinstance(fn, str):
                return to
            try:
                args = inspect.getargspec(getattr(fn, "__init__", lambda:None))
            except:
                return []
            methods = dict(filter(lambda i: not inspect.ismethod(i[1]) and callable(i[1]), fn.__dict__.iteritems()))
            if not methods:
                raise Exception("How to access a variable that's don't aparently exists?")
            if methods.keys()[1:]:
                arg = args[0][1]
                if not methods.has_key(arg):
                    raise Exception("Not possible to recognize where the function is saved in decorator. Options available:%s" % "".join(methods.keys()))
                fn = methods[arg]
            else:
                fn = fn.values()[0]
                
            to.append(fn)
        if not getattr(fn, "func_closure", []):
            if natural_order:
                to.reverse()
            return to
        if not to:
            to.append(fn)
        to.append(fn.func_closure[0].cell_contents)
        return BaseUtils.getDecoratorHistory(to[-1], natural_order, to)
