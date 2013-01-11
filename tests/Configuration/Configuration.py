'''
Created on 06/01/2013

@author: fernando
'''
import sys, os
sys.path.insert(0, os.path.realpath(os.path.join(os.getcwd(), "..","..")))
from config.Configuration import Configuration
config = Configuration.getInstance()
f = config.load("config.ini")
opt = config.getOption("dir")
print opt.getValue(), "(",type(opt.getValue()),")"
opt = config.getOption("foodir")
print opt.getValue(), "(",type(opt.getValue()),")"
sect = config.getSection("teste2").getSection("teste")
if sect:
    opt =  sect.getOption("galera")
    print opt.getValue(), "(",type(opt.getValue()),")"
    opt =  sect.getOption("risos")
    print opt.getValue(), "(",type(opt.getValue()),")"
print config.getPath("teste/risos").getValue()
print f.toDict(True, True, True)