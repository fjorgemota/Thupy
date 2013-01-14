'''
Created on 05/01/2013

@author: fernando
'''
import inspect
from utils.BasicClass.AbstractInterfaceType import AbstractInterfaceType
class abstract(object):
    __metaclass__ = AbstractInterfaceType
def abstractFn(fn):
    fn.__implemented__ = False
    fn.__arguments__ = inspect.getargspec(fn)
    fn.__is_static__ = not inspect.ismethod(fn)
    return fn