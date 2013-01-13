import sys, os
sys.path.insert(0, os.path.realpath(os.path.join(os.getcwd(), "..","..")))
#from utils.PackageManager import PackageManager
#PackageManager.importPackage("pyximport","cython") #Import the package pyximport that's installed with Cython
#pyximport.install(pyimport=True, inplace=True, build_in_temp=False) #There's now in the global space, i await
import random, time, traceback, logging, Queue, os, inspect, threading
#logging.basicConfig(level=logging.INFO)
from utils.MicroThread import MicroThread, MicroThreadPoll, microThreadDecorator, OrderedPrint
try: 
    import cython
except ImportError:
    cython = None
num_thread = raw_input("Informe quantas threads devem ser usadas para execucao do teste (padrao = Numero de cores do seu PC)")
if not num_thread.isdigit():
    num_thread = True
else:
    num_thread = int(num_thread)
MicroThreadPoll.getInstance(num_thread)
MicroThreadPoll.startAll()
#def soma():
#    n1 = (yield "Numero 1")
#    n2 = (yield "Numero 2")
#    yield "O resultado da soma eh %d"%(n1+n2)
#def callback(thread, mode, result=None):
#    if mode == "yield":
#        if thread.isWaiting():
#            thread.send(int(raw_input(result)))
#        else:
#            print result
#print MicroThreadPoll.parse(soma)
#print MicroThreadPoll.parse(callback)
#t = MicroThread(soma)
#t.addCallback(callback)
#t.start()
#MicroThreadPoll.startAll()
try:
    import cProfile as profile
except:
    import profile
if cython:
    @cython.locals(n=cython.int, resultado=cython.longlong, num=cython.int)
    @cython.returns(cython.longlong)
    @microThreadDecorator
    def slowFactorial(n):
        resultado = 1
        for num in xrange(1, n+1):
            resultado = resultado*num
        return resultado
    @cython.locals(num=cython.longlong, resultado=cython.longlong)
    @cython.returns(cython.longlong)
    def factorialMult(num, resultado):
        return num*resultado
    @cython.locals(n=cython.longlong)
    @cython.returns(cython.longlong)
    @microThreadDecorator
    def factorial(n):
        return reduce(factorialMult,xrange(1, n+1))
else:
    @microThreadDecorator
    def slowFactorial(n):
        resultado = 1
        for num in xrange(1, n+1):
            resultado = resultado*num
        return resultado
    def factorialMult(num, resultado):
        return num*resultado
    @microThreadDecorator
    def factorial(n):
        return reduce(factorialMult,xrange(1, n+1))
def dec(fn):
    def wrapper(*args, **kwargs):
        print "RISOS"
        r = fn(*args, **kwargs)
        print ":D"
        print r
        return r
    wrapper.__name__ = fn.__name__
    for attr in dir(fn):
        if "microThread" not in attr:
            continue
        setattr(wrapper, attr, getattr(fn, attr))
    return wrapper
__builtins__.dec = dec
@dec
@microThreadDecorator
def page():
    return 'HTTP/1.1 200\r\nContent-type:text/html\r\n\r\nHello, world'
def microThreadCompareBenchmark(cb, num_count=100, parseFuncs=False, *args,**kwargs):
    if not getattr(cb, "microThreadDecorated", False):
        raise Exception("Callback not supported. Decorate it with @microThreadDecorator :~~")
        return False
    print "-"*50, cb.__name__," inline","-"*50
    print "Processando ",cb.__name__," inline"
    inline_times = []
    #OrderedPrint.getInstance().setPriority(sys.maxint/2)
    for n in xrange(0, num_count):
        init_inline_time = time.time()
        cb(microThread_enable=False, *args, **kwargs)
        final_inline_time = time.time()
        #time.sleep(0.00000000000001)
        inline_times.append(final_inline_time-init_inline_time)
    total_inline_time = sum(inline_times)
    avg_inline_time = total_inline_time/num_count
    min_inline_time = min(inline_times)
    max_inline_time = max(inline_times)
    print "Processado inline em ",total_inline_time," segundos (funcao ",cb.__name__,")"
    print "Os itens foram processados em uma media de ",avg_inline_time," segundos (funcao ",cb.__name__,")"
    print "O item mais rapido foi processado em ",min_inline_time," segundos (funcao ",cb.__name__,")"
    print "O item mais lento foi processado em ",max_inline_time," segundos (funcao ",cb.__name__,")"
    
    print "-"*50,cb.__name__," com micro-threads sequenciais", "-"*50
    print "Adicionando itens de micro-threads seriais"
    micro_threads = [cb(microThread_autoStart=False, microThread_parseFuncs=parseFuncs, *args, **kwargs) for n in xrange(0, num_count)]
    print "Processando ",cb.__name__," com micro-threads seriais"
    serial_times = []
    for micro_thread in micro_threads:
        init_serial_time = time.time()
        micro_thread.start()
        micro_thread.join()
        final_serial_time = time.time()
        #serial_times.append(micro_thread.getTimeRunning())
        serial_times.append(final_serial_time-init_serial_time)
    total_serial_time = sum(serial_times)
    avg_serial_time = total_serial_time/num_count
    min_serial_time = min(serial_times)
    max_serial_time = max(serial_times)
    print "Processado com as micro-threads sequenciais em ",total_serial_time," segundos (funcao ",cb.__name__," com micro-threads sequenciais)"
    print "Os itens foram processados em uma media de ",avg_serial_time," segundos (funcao ",cb.__name__," com micro-threads sequenciais)"
    print "O item mais rapido foi processado em ",min_serial_time," segundos (funcao ",cb.__name__," com micro-threads sequenciais)"
    print "O item mais lento foi processado em ",max_serial_time," segundos (funcao ",cb.__name__," com micro-threads sequenciais)"
    print "-"*50,cb.__name__," com micro-threads simultaneas","-"*50
    print "Adicionando itens de micro-threads simultaneas"
    micro_threads = [cb(microThread_autoStart=False, microThread_parseFuncs=parseFuncs, *args, **kwargs) for n in xrange(0, num_count)]
    print "Processando ",cb.__name__," com micro-threads simultaneas"
    map(MicroThread.start, micro_threads)
    #map(lambda micro_thread: micro_thread.setPriority(4000000), micro_threads)
    map(MicroThread.join, micro_threads)
    real_times = map(MicroThread.getTimeRunning, micro_threads)
    total_real_time = sum(real_times)
    avg_real_time = total_real_time/num_count
    min_real_time = min(real_times)
    max_real_time = max(real_times)
    print "Processado com as micro-threads simultaneas em ",total_real_time," segundos (funcao ",cb.__name__," com micro-threads simultaneas)"
    print "Os itens foram processados em uma media de ",avg_real_time," segundos (funcao ",cb.__name__," com micro-threads simultaneas)"
    print "O item mais rapido foi processado em ",min_real_time," segundos (funcao ",cb.__name__," com micro-threads simultaneas)"
    print "O item mais lento foi processado em ",max_real_time," segundos (funcao ",cb.__name__," com micro-threads simultaneas)"
    print "-"*50,"Resumo","-"*50
    names = ["inline","micro-thread serial","micro-thread simultanea"]
    total_times = [total_inline_time, total_serial_time, total_real_time]
    avg_times = [avg_inline_time, avg_serial_time, avg_real_time]
    min_times = [min_inline_time, min_serial_time, min_real_time]
    max_times = [max_inline_time, max_serial_time, max_real_time]
    print "Itens mais rapidos:"
    print "O item mais rapido considerando o tempo total foi: ",names[total_times.index(min(total_times))]," (com ",min(total_times)," segundos)"
    print "O item mais rapido considerando a media de processamento de cada item foi: ",names[avg_times.index(min(avg_times))]," (com ",min(avg_times)," segundos)"
    print "O item mais rapido considerando o item processado mais rapido foi: ",names[min_times.index(min(min_times))]," (com ",min(min_times)," segundos)"
    print "O item mais rapido considerando o item processado mais lento foi: ",names[max_times.index(min(max_times))]," (com ",min(max_times)," segundos)"
    print "Itens mais lentos:"
    print "O item mais lento considerando o tempo total foi: ",names[total_times.index(max(total_times))]," (com ",max(total_times)," segundos)"
    print "O item mais lento considerando a media de processamento de cada item foi: ",names[avg_times.index(max(avg_times))]," (com ",max(avg_times)," segundos)"
    print "O item mais lento considerando o item processado mais rapido foi: ",names[min_times.index(max(min_times))]," (com ",max(min_times)," segundos)"
    print "O item mais lento considerando o item processado mais lento foi: ",names[max_times.index(max(max_times))]," (com ",max(max_times)," segundos)"
def main():
    parseFuncs = raw_input("Ativar parseamento de funcoes? (S/N)").upper() == "S"
    num_count = raw_input("Informe o numero de vezes que o procedimento deve ser repetido:")
    if not num_count.isdigit() or not num_count.strip():
        print "Nao sabia que isso e um numero..Setando logo pra 1000 xD"
        num_count = 1000
    num_count = int(num_count)
    microThreadCompareBenchmark(page, num_count, parseFuncs)
def mainFactorial():
    parseFuncs = raw_input("Ativar parseamento de funcoes? (S/N)").upper() == "S"
    num = raw_input("Informe um numero para calcularmos o fatorial:")
    if not num.isdigit() or not num.strip():
        print "Nao sabia que isso e um numero..Setando logo pra 100 xD"
        num = 100
    num = int(num)
    num_count = raw_input("Informe o numero de vezes que o calculo deve ser repetido:")
    if not num_count.isdigit() or not num_count.strip():
        print "Nao sabia que isso e um numero..Setando logo pra 1000 xD"
        num_count = 1000
    num_count = int(num_count)
    microThreadCompareBenchmark(factorial, num_count, parseFuncs, num)
    microThreadCompareBenchmark(slowFactorial, num_count, parseFuncs, num)
    
if __name__ == "__main__":
    #mainFactorial()
    main()
    time.sleep(2)
    while True:
        try:
            line = raw_input(">>").strip()
            if not line:
                line = "exit()"
            r = eval(line)
            if r:
                print r
        except KeyboardInterrupt:
            break
        except Exception, e:
            print traceback.format_exc()
            continue
#for r in range(last_count):
#    if OrderedPrint.getInstance().getCount() == last_count*2:
#        print "Encerrando.."
#        micro_threads = [] 
#        while True:
#            t = MicroThreadPoll.getInstance()
#            if micro_threads.count(t) == 5:
#                break
#            t.stop()
#            micro_threads.append(t)
#        os._exit(0)
#        continue
#    OrderedPrint.getInstance().join()
#    time.sleep(10)
