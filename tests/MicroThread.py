import sys, random, time, traceback, logging, Queue, os, inspect
#logging.basicConfig(level=logging.DEBUG)
sys.path.insert(0, "../")
from utils.MicroThread import MicroThread, MicroThreadPoll, microThreadDecorator, OrderedPrint
MicroThreadPoll.getInstance(True)
OrderedPrint.getInstance().install()
last_count = 10
def test2(a=None,*args,**kwargs):
    return a.upper()
def test3():
    pass
def test(a,*args,**kwargs):
    pass
@microThreadDecorator
def page(inline=False):
    init_personal_time = time.time()
    _resp = ["HTTP/1.1 200\r\nContent-Type: text/html\r\n\r\n"]
    _resp.extend("Hello World")
    final_personal_time = time.time()
    if inline:
        msg = "Processado (inline) em "+str(final_personal_time-init_personal_time)+" segundos"
    else:
        msg = "Processado em "+str(final_personal_time-init_personal_time)+" segundos"
    test2(msg,rs='oi',aheuahue=test("risos", lol='risos', fala='GALERA'))
    m = test2(msg, lol=test(a=None,b='FALA GALERA'), rs=test3())
    print m
    yield {"resp":_resp,"time":final_personal_time-init_personal_time}
def callback(*args):
    print args
print "Adicionando Micro-threads :B"
micro_threads = []
for n in xrange(0, last_count):
    #th = MicroThread(page)
    #th.start()
    th = page()
    #th.addCallback(callback)
    th.suspend()
    micro_threads.append(th)
print "Processando inline.."
init_slow_time = time.time()
OrderedPrint.getInstance().setPriority(sys.maxint/2)
for n2 in xrange(0, last_count):
    t = page(micro_thread_enable=False, inline=False)
    time.sleep(0.00000000000001)
final_slow_time = time.time()
print final_slow_time-init_slow_time," segundos"
init_time = time.time()
for instance in MicroThreadPoll.getInstances():
    print "Iniciando...", instance
    instance.start()
for r in range(last_count):
    if OrderedPrint.getInstance().getCount() == last_count:
        break
    OrderedPrint.getInstance().join()
print "O Codigo modificado da Micro-Thread ficou assim:"
print MicroThreadPoll.parse(page.oldFunc, True)
raw_input("Aperte ENTER quando for pra iniciar a Micro-Thread")
OrderedPrint.getInstance().setPriority(100)
print "Iniciando Micro-Threads"
map(MicroThread.resume, micro_threads)
for r in range(last_count):
    if OrderedPrint.getInstance().getCount() == last_count*2:
        print "Encerrando.."
        micro_threads = [] 
        while True:
            t = MicroThreadPoll.getInstance()
            if micro_threads.count(t) == 5:
                break
            t.stop()
            micro_threads.append(t)
        os._exit(0)
        continue
    OrderedPrint.getInstance().join()
    time.sleep(10)
