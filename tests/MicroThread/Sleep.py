'''
Created on 19/01/2013

@author: fernando
'''
import sys, os, time
sys.path.insert(0, os.path.realpath(os.path.join(os.getcwd(), "..", "..")))
from utils.MicroThread import MicroThread, MicroThreadPoll
MicroThreadPoll.getInstance(True)
print "Iniciando instancias.."
MicroThreadPoll.startAll()
def justSleep():
    print "Dormindo.."
    time.sleep(5)
    print "Terminou de dormir..xD"

microthreads = []
for _ in xrange(100):
    print "Criando micro-thread.."
    microthread = MicroThread(justSleep)
    print "Iniciando micro-thread.."
    microthread.start()  # Put in the queue!
    microthread.setTimeout(5.1)
    print "Adicionando a lista.."
    microthreads.append(microthread)

for microthread in microthreads:
    print "Aguardando.."
    microthread.join()
    print "Terminou de aguardar.."
