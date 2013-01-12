'''
Created on 10/01/2013

@author: fernando
Fallback to allow use of the Thupy in implementations that do not have the itertools module
'''
try:
    from itertools import chain #Native is the best xD
except ImportError:
    #Only the functions that we need....
    def chain(*iterables):
        # chain('ABC', 'DEF') --> A B C D E F
        for it in iterables:
            for element in it:
                yield element