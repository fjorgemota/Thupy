'''
Created on 15/08/2012

@author: fernando
'''
import inspect,cython
__all__ = ["interface","abstract","abstract_method"]
@cython.ccall
def abstract_method(fn):
    def abstract_fn(*args,**kwargs):
        if fn.func_name in ("__init__","__new__"):
            raise NotImplementedError("".join(["The constructor is not implemented or this class cannot be instantiated"]))
            return None
        raise NotImplementedError("".join(["The function '",str(fn.func_name),"' is not implemented"]))
    abstract_fn.__name__ = fn.__name__
    abstract_fn.__abstract__ = True
    abstract_fn.__implemented__ = True
    abstract_fn.__arguments__ = inspect.getargspec(fn)
    return abstract_fn
@cython.locals(name=str, val=str, parents=object)
def __isAttrEqual(name, val, parents):
    for parent in parents:
        if getattr(parent, name) == val:
            return True
    return False
@cython.cclass
class abstract(type):
    @cython.ccall
    @cython.locals(self=type,
                   name=str,
                   parents=list,
                   attrs=dict, 
                   new_attrs=list,
                   is_subclass=bool, 
                   bases_attrs = dict,
                   parent_attr_name=str,
                   parent_attr_val = object,
                   val=object,
                   the_metaclass=object
                   )
    def __new__(self, name, parents=[], attrs={}):
        if not isinstance(name, str):
            name.__implemented__ = False
            return name
        new_attrs = []
        is_subclass = not attrs.has_key("__metaclass__")
        bases_attrs = {}
        for parent in parents:
            if getattr(parent, "__metaclass__",None) == abstract:
                parent_attrs = dir(parent)
                for parent_attr_name in parent_attrs:
                    parent_attr_val = getattr(parent, parent_attr_name)
                    if inspect.isfunction(parent_attr_val):
                        bases_attrs[parent_attr_name] = getattr(parent_attr_val,"__arguments__",inspect.getargspec(parent_attr_val))
        if not attrs.has_key("__init__"):
            def __init__(*args, **kwargs):
                pass
            if not is_subclass:
                __init__.__implemented__ = True
            attrs["__init__"] = __init__
        elif is_subclass and getattr(attrs.get("__init__"),"__implemented__", False):
            def __init__(*args, **kwargs):
                pass
            __init__.__implemented__ = True
            attrs["__init__"] = __init__
        for name, val in attrs.iteritems():
            if inspect.isfunction(val):
                print name," = ",is_subclass," and ((not ",getattr(val,"__implemented__",True)," and ",bases_attrs.get(name)," == ",inspect.getargspec(val),") or ",bases_attrs.get(name)," != ",inspect.getargspec(val),")"
                if not is_subclass and not getattr(val,"__implemented__",True):
                    val = abstract_method(val)
                elif is_subclass and ((not getattr(val,"__implemented__",True) and bases_attrs.get(name) == inspect.getargspec(val)) or bases_attrs.get(name) != inspect.getargspec(val)):
                    raise NotImplementedError("".join(["Method don't overrided (with the same arguments) in the class '",name,"' that's implements a interface"]))
                    continue
            new_attrs.append((name,val))
        new_dict = dict(new_attrs)
        the_metaclass = type.__new__(self,name,parents,new_dict)
        return the_metaclass
@cython.cclass
class interface(type):
    @cython.ccall
    @cython.locals(self=type,
                   name=str,
                   parents=list,
                   attrs=dict, 
                   new_attrs=list,
                   is_subclass=bool, 
                   bases_attrs = dict,
                   parent_attr_name=str,
                   parent_attr_val = object,
                   val=object,
                   the_metaclass=object
                   )
    def __new__(self, clsname, parents=[], attrs={}):
        new_attrs = []
        is_subclass = not attrs.has_key("__metaclass__")
        if not attrs.has_key("__init__"):
            def __init__(*args, **kwargs):
                pass
            if is_subclass:
                __init__.__abstract__ = False
            attrs["__init__"] = __init__
        elif is_subclass and getattr(attrs.get("__init__"),"__abstract__", False):
            def __init__(*args, **kwargs):
                pass
            __init__.__abstract__ = False
            attrs["__init__"] = __init__
        for name, val in attrs.iteritems():
            if name == "__metaclass__":
                continue
            print "Verificando metodo ",name,"=",val
            if not is_subclass and callable(val) and not getattr(val,"__abstract__",False):
                val = abstract_method(val)
            elif is_subclass and getattr(val,"__abstract__",False):
                raise NotImplementedError("".join(["Method don't overrided in the class '",name,"' that's implements a interface"]))
                continue
            new_attrs.append((name,val))
        new_dict = dict(new_attrs)
        print new_dict
        the_metaclass = type.__new__(self, clsname,parents,new_dict)
        return the_metaclass