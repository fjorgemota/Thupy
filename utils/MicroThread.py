import inspect, tokenize, itertools, threading, string, random, sys, os, time, re, logging as _logging, Queue, types, atexit, __builtin__, shutil
try:
    from hashlib import md5
except ImportError:
    from md5 import md5    
try:
    import multiprocessing
except ImportError:
    multiprocessing = None
try:
    from pyximport.pyxbuild import pyx_to_dll
except:
    pyx_to_dll = None
from utils.functools import partial
from utils.BasicClass.enum import enum
logging = _logging.getLogger("MicroThread")
class MicroThreadSignals(enum):
    RETURN = None
    YIELD = None
    YIELD_AWAIT_RESULT = None
    KILLED = None
    TIMEOUTED = None
    SIMPLE_PASS = None
    CALL_FUNCTION = None
class MicroThreadCallbacksMode(enum):
    RETURN = None
    YIELD = None
    YIELD_AWAIT_RESULT = None
    KILLED = None
    TIMEOUTED = None
    ALL = None
__builtin__.MicroThreadCallbacksMode = MicroThreadCallbacksMode
class SimpleGenerator(object):
    '''Simulates a Generator'''
    def __init__(self, receiver, sender):
        self.yieldQueue = Queue.Queue()
        self.sendQueue = Queue.Queue()
        self.receiver = receiver
        self.endFlag = False
        self.sender = sender
        self.sender.addCallback(self.manageCallback)
        self.sender.suspend()
        self.receiver.send(self)
    def __iter__(self):
        return self
    def next(self):
        self.sender.resume()
        while True:
            if self.endFlag:
                raise StopIteration()   
            try:
                return self.yieldQueue.get_nowait()
            except Queue.Empty:
                continue
    def send(self, msg):
        while True:
            try:
                self.sendQueue.put_nowait(msg)
            except:
                continue
            break
    def throw(self, type_exception, *args, **kwargs):
        self.sender.throw(type_exception,*args,**kwargs)
    def manageCallback(self, thread, mode, item):
        if mode == MicroThreadCallbacksMode.YIELD:
            while True:
                try:
                    self.yieldQueue.put_nowait(item)
                except:
                    continue
                break
            if thread.isWaiting():
                while True:
                    try:
                        m= self.sendQueue.get_nowait()
                    except Queue.Empty:
                        continue
                    thread.send(m)
                    break
        elif mode == MicroThreadCallbacksMode.RETURN:
            self.endFlag = True
class MicroThreadTask(object):
    def __init__(self, thread, fn, localVars, globalVars, args, kwargs):
        self.thread = thread
        self.task = fn(thread, localVars, globalVars, *args, **kwargs)
        self.timeout = None
        self.suspended = False
        self.killed = False
        self.time_processing = 0
        self.priority = 100
        self.count = 0
        self.to_send = Queue.Queue() #Queue to put itens to send
        self.need_send = False
        self.running = threading.Lock() # A lock to detect if it's running or no
        self.terminated = threading.Event() #Flag with terminated event
        self.result = []#Put's in ALL the results emited by the MicroThread
        self.result_lock = threading.Lock() #A lock to block modifications in self.result during iteration
        self.result_queues = [] #A list of queues to put in new results during the execution of MicroThread
        self.result_sended = False#Only a flag to indicate if a call to waitResult() have or not access to send..
    def setTimeout(self, timeout):
        self.timeout = timeout
    def setPriority(self, priority):
        self.priority = priority
        self.count = 0
    def suspend(self):
        if self.suspended:
            return
        logging.debug("Suspendendo tarefa")
        self.suspended = True
        MicroThreadPoll.remove(self)
    def send(self,msg):
        logging.debug("Adicionando informacao %s ao queue para envio posterior"%str(msg))
        self.to_send.put_nowait(msg)
        self.resume()
    def resume(self):
        if not self.suspended:
            return
        logging.debug("Resumindo tarefa")
        self.suspended = False
        MicroThreadPoll.add(self)
    def isSuspended(self):
        return self.suspended
    def kill(self):
        self.killed = True
    def throw(self, type_exception, *args, **kwargs):
        logging.debug("Criando excecao no generator")
        self.task.throw(type_exception, *args, **kwargs)
    def join(self):
        self.terminated.wait()
        return True
    def waitResult(self, oldResult=False, send=False):
        self.result_lock.acquire() #To not modify the list..xD
        queue = Queue.Queue()
        self.result_queues.append(queue)
        if not inspect.isgeneratorfunction(self.run):
            send = False
        if send and self.result_sended:
            raise Exception("Allowed only one sender by Micro-Thread")
            send = False
        if send:
            #Yields all the values, and, if needed, it can send values too!
            self.result_sended = True
            instance = self
            def waitResult():
                if oldResult:#Only if this flag is True
                    for result in instance.result:#Iter all, but only return one xD
                        yield result #Just return
                    instance.result_locks.release() #Release the lock to continue execution
                try:
                    while True:
                        res = queue.get()#blocks..
                        if res["mode"] == MicroThreadCallbacksMode.TIMEOUTED:
                            raise Exception("MicroThread timeouted!")
                        elif res["mode"] == MicroThreadCallbacksMode.KILLED:
                            raise Exception("Microthread killed!")
                        elif res["mode"] == MicroThreadCallbacksMode.YIELD:
                            yield res["result"] #Just Yield!
                        elif res["mode"] == MicroThreadCallbacksMode.YIELD_AWAIT_RESULT:
                            instance.send((yield res["result"])) #Yields a value and wait another to send..xD
                        else:
                            break #Just break!
                finally:#Just closes the generator
                    instance.result_sended = False
        else:
            instance = self
            if inspect.isgeneratorfunction(self.run):
                #Yields all the values, and, if needed, but it can't send values too!
                def waitResult():
                    if oldResult:#Only if this flag is True
                        for result in instance.result:#Iter all, and yield all too
                            yield result #Yield the value..xD
                        instance.result_locks.release() #Release the lock to continue execution
                    while True:
                        res = queue.get()#blocks..
                        if res["mode"] == MicroThreadCallbacksMode.TIMEOUTED:
                            raise Exception("MicroThread timeouted!")
                        elif res["mode"] == MicroThreadCallbacksMode.KILLED:
                            raise Exception("Microthread killed!")
                        elif res["mode"] in (MicroThreadCallbacksMode.YIELD,MicroThreadCallbacksMode.YIELD_AWAIT_RESULT):
                            yield res["result"] #Just Yield!
                        else:
                            break #Just break!
            else:
                #Just return a value xD
                def waitResult():
                    if oldResult:#Only if this flag is True
                        for result in instance.result:#Iter all, but only return one xD
                            return result #Just return
                        instance.result_locks.release() #Release the lock to continue execution
                    res = queue.get() #Blocks..
                    if res["mode"] == MicroThreadCallbacksMode.TIMEOUTED:
                        raise Exception("MicroThread timeouted!")
                    elif res["mode"] == MicroThreadCallbacksMode.KILLED:
                        raise Exception("Microthread killed!")
                    return res["result"]
        return waitResult() #A function can't be a generator or return a result at the same time, and this allows the two possibilities to be realized at the same time and in any implementation. xD
    def isWaiting(self):
        return self.need_send
    def isRunning(self):
        return self.lock.locked()
    def next(self):
        self.count += self.priority
        while self.count > 100:
            init_time = time.time()
            try:
                if self.need_send:
                    logging.debug("Aguardando informacao")
                    try:
                        m = self.to_send.get_nowait()
                    except:
                        self.count -= 100
                        final_time = time.time()
                        self.time_processing += final_time - init_time
                        continue
                    self.to_send.task_done()
                    logging.debug("Enviando informacao")
                    result = self.task.send(m)
                    self.need_send = False
                else:
                    result = self.task.next()
            except StopIteration:
                result = [1]
            final_time = time.time()
            self.time_processing += final_time - init_time
            if self.killed:
                logging.debug("Matando tarefa")
                self.terminated.set()
                self.result_lock.acquire()
                result_to_queue = {"mode":MicroThreadCallbacksMode.KILLED,"result":None}
                self.result.append(result_to_queue)
                map(lambda q: q.put_nowait(result_to_queue), self.result_queues)
                self.result_lock.release()
                self.thread.callCallback(MicroThreadCallbacksMode.KILLED, [])
                try:
                    self.task.close()
                except GeneratorExit:
                    pass
                raise StopIteration()
                break
            elif self.timeout != None and self.timeout < self.time_processing:
                logging.debug("Retornando timeout")
                self.terminated.set()
                self.result_lock.acquire()
                result_to_queue = {"mode":MicroThreadCallbacksMode.TIMEOUTED,"result":None}
                self.result.append(result_to_queue)
                map(lambda q: q.put_nowait(result_to_queue), self.result_queues)
                self.result_lock.release()
                self.thread.callCallback(MicroThreadCallbacksMode.TIMEOUTED, [])
                try:
                    self.task.close()
                except GeneratorExit:
                    pass
                raise StopIteration()
                break
            elif result[0] == MicroThreadSignals.SIMPLE_PASS:
                pass #Just to not execute the other "elif" statements =Pz
            elif result[0] == MicroThreadSignals.RETURN:
                logging.debug("Retornando resultado da tarefa")
                self.terminated.set()
                self.result_lock.acquire()
                arg = result[1:]
                if not arg[1:] and arg:
                    arg = arg[0]
                elif not arg:
                    arg = None
                result_to_queue = {"mode":MicroThreadCallbacksMode.RETURN,"result":arg}
                self.result.append(result_to_queue)
                map(lambda q: q.put_nowait(result_to_queue), self.result_queues)
                self.result_lock.release()
                self.thread.callCallback(MicroThreadCallbacksMode.RETURN, result[1:])
                try:
                    self.task.close()
                except:
                    pass
                raise StopIteration()
                break
            elif result[0] in (MicroThreadSignals.YIELD,MicroThreadSignals.YIELD_AWAIT_RESULT):
                logging.debug("Retornando yield")
                self.need_send = result[0] == MicroThreadSignals.YIELD_AWAIT_RESULT
                self.thread.callCallback([MicroThreadCallbacksMode.YIELD, MicroThreadCallbacksMode.YIELD_AWAIT_RESULT][self.need_send], result[1:])
                if self.need_send:
                    logging.debug("Aguardando resultado")
                    self.suspend()
            elif result[0] == MicroThreadSignals.CALL_FUNCTION:
                logging.debug("Chamando funcao %s"%result[1].__name__)
                self.need_send = True
                if result[3].pop("microThread_enable", True):
                    priority = result[3].pop("microThread_priority", self.priority)
                    timeout = result[3].pop("microThread_timeout", None)
                    try:
                        mt = MicroThread(result[1], *result[2],**result[3])
                        self.suspend()
                        if inspect.isgeneratorfunction(result[1]):
                            SimpleGenerator(self.thread, mt)
                        else:
                            parent = self
                            def returnCallback(thread, mode, result):
                                if mode == "return":
                                    logging.debug("Retornando chamada da funcao")
                                    parent.send(result)
                            returnCallback.microThread_globals = {"parent":self}
                            returnCallback.microThread_enable = False
                            mt.addCallback(returnCallback)
                        mt.start()
                        mt.setPriority(priority)
                        if not timeout and self.getTimeout():
                            timeout = self.getTimeout()-self.getTimeRunning()
                        mt.setTimeout(timeout)
                    except:
                        try:
                            self.send(result[1](*result[2],**result[3]))
                        except Exception, e:
                            self.throw(type(e), e.message)
                        mt = None                       
                else:
                    try:
                        self.send(result[1](*result[2],**result[3]))
                    except Exception, e:
                        self.throw(type(e), e.message)
            self.count -= 100 
    def getThread(self):
        return self.thread
    def getPriority(self):
        return self.priority
    def getTimeout(self):
        return self.timeout
    def getTimeRunning(self):
        return self.time_processing
    def getTask(self):
        return self.task
class MicroThreadPoll:
    instance = None
    tasks = Queue.Queue()
    to_remove = []
    size = 0
    count = 0
    funcs = {True:{},False:{}}
    codes = {True:{},False:{}}
    temp_dir = None
    def __init__(self):
        self.thread = False
        self.stopFlag = True
        self.suspendFlag = threading.Event()
        self.suspendFlag.set()
    def suspend(self):
        self.clear()
    def stop(self):
        self.stopFlag = True
    def resume(self):
        self.set()
    def isRunning(self):
        return not self.stopFlag and not self.sleepFlag
    def setThread(self, thread):
        self.thread = thread
    def isThread(self):
        return self.thread is True
    @staticmethod
    def add(task):
        logging.debug("Adicionando...")
        return MicroThreadPoll.tasks.put_nowait(task.next) #It's never be full =P
    @staticmethod
    def remove(task):
        logging.debug("Removendo..")
        MicroThreadPoll.to_remove = itertools.chain(MicroThreadPoll.to_remove, [task]) #Adds to the iterator xD
    @staticmethod
    def join():
        return MicroThreadPoll.tasks.join()
    @staticmethod
    def getFunction(thread):
        if isinstance(thread, MicroThread):
            code = thread.run
        else:
            code = thread
        return code
    @staticmethod
    def getHash(thread):
        code = MicroThreadPoll.getFunction(thread)
        if inspect.isbuiltin(code):
            return ""
        else:
            code = inspect.getsource(code)
        logging.info("Cadastrando nova funcao")
        logging.debug("Codificando funcao")
        func_hash = list(md5(code).hexdigest())
        if func_hash[0].isdigit():
            func_hash.insert(0, "h")
        return "".join(func_hash)
    @staticmethod
    def parse(thread, parseFuncs = True):
        func = MicroThreadPoll.getFunction(thread)
        if inspect.isbuiltin(func):
            raise TypeError("Can't manipulate builtins code")
        elif not isinstance(func, str):
            code = inspect.getsource(func)
        func_hash = MicroThreadPoll.getHash(thread)
        parseFuncs = getattr(func, "microThread_parseFuncs", parseFuncs)
        if MicroThreadPoll.codes[parseFuncs].has_key(func_hash):
            return MicroThreadPoll.codes[parseFuncs][func_hash]
        logging.debug("Parseando funcao")
        opened = True
        lines = code.strip().split("\n")
        tab = ["    ", "\t"][code.count("\t") > 0]
        is_method = code.startswith(tab)
        tab_length = len(tab)
        copy_lines = filter(lambda line: "@cython.ccall" not in line, lines)
        if copy_lines != lines:
            logging.warning("Don't use the decorator cython.ccall with micro-threads: that don't work!")
            lines = copy_lines
        lines = filter(lambda line: "@microThreadDecorator" not in line, lines)
        func_name = filter(lambda line: "def" in line, lines)[0].split("def ", 1)[1].split("(", 1)[0] 
        logging.debug("O nome da funcao e %s" % func_name)
        new_lines = []
        temp_code = []
        init = None
        dont_work = False
        for line in lines:
            logging.debug("Processando nova linha")
            returnSome = False
            yieldSome = False
            dont_work = False
            if is_method and line.startswith(tab):
                line = line[tab_length:]
            try:    
                if opened:
                    temp_code.append(line)
                else:
                    temp_code = [line]               
                logging.debug("Tokenizando codigo")
                tokens = tokenize.generate_tokens(iter(temp_code).next)
                for token in tokens:
                    #print parenteses
                    if token[1] in ("else", "elif", "except", "finally", "@", "def"):
                        dont_work = True
                    elif token[0] == tokenize.COMMENT: 
                        dont_work = True
                    if token[1] == "return":
                        logging.debug("Statement return detectado")
                        returnSome = token
                    elif token[1] == "yield":
                        logging.debug("Statement yield detectado")
                        yieldSome = token
                    continue
                opened = False
                #if not dont_work and line.count(tab) != actual_tab_count:
                #    dont_work = True
                #    actual_tab_count = line.count(tab)
            except:
                logging.debug("Linha nao-terminada, pulando...")
                opened = True
            if returnSome:
                logging.debug("Substituindo return")
                line = list(line)
                line[returnSome[2][1]:returnSome[3][1]] = "yield MicroThreadSignals.RETURN,"
                line = "".join(line) 
            elif yieldSome:
                logging.debug("Substituindo yield")
                line = list(line)
                line[yieldSome[2][1]:yieldSome[3][1]] = "yield "+["MicroThreadSignals.YIELD","MicroThreadSignals.YIELD_AWAIT_RESULT"][line[yieldSome[2][1]-1]=="("]+","
                line = "".join(line) 
            if not opened and not temp_code[1:] and not dont_work:
                logging.debug("Atualizando funcao...")
                if not init:
                    init = (line.count(tab) * tab)
                new_lines.append((line.count(tab) * tab) + "yield MicroThreadSignals.SIMPLE_PASS,")
            if not opened: 
                dont_work = False
            logging.debug("Adicionando nova linha")
            new_lines.append(line)
        #func_name = fn_names[0][0]
        #fn_names.reverse()
        first = True
        while True:
            if not first and not parseFuncs:
                break
            tokens = list(tokenize.generate_tokens(iter(new_lines).next))
            to_modify = {}
            parenteses = [0]
            fn_name = [None]
            fn_names = []
            banned_words = ["yield","return","def","dict","items","globals","locals", "global", "if", "else","for","cython","with","while","in","not"]+dir(__builtin__)
            count = 0
            func_locals = []
            last_token = None
            func_defined = [0]
            funcs_defined = [None]
            vars_used = []
            vars_banned = []
            for token in tokens:
                if fn_name[-1] and token[0] == tokenize.NAME and token[1] not in banned_words and parenteses[-1] == 0:
                    fn_name[-1].append(token)
                    if func_defined[-1]:
                        funcs_defined[-1].append(token)
                elif token[0] == tokenize.NAME and token[1] not in banned_words:
                    is_fn = False
                    dot = False
                    is_var = tokens[count+1][1] != "=" and token[1] not in vars_banned and token[1] not in func_name
                    if last_token and is_var:
                        is_var = last_token[1] not in (".","for")
                    if is_var:
                        vars_used.append(token[1])
                    else:
                        vars_banned.append(token[1])
                    for temp_token in tokens[count+1:]:
                        if temp_token[0] == tokenize.OP:
                            if temp_token[1] == ".":
                                dot = True
                            elif temp_token[1] == "(":
                                is_fn = True
                            else:
                                break
                        elif temp_token[0] == tokenize.NAME and dot:
                            continue
                        else:
                            break
                    if last_token:
                        if last_token[0] == tokenize.OP and last_token[1] in (".","@"):
                            is_fn = False
                    if is_fn:
                        func_defined.append([0, 1][last_token[1] == "def"])
                        if func_defined[-1]:
                            funcs_defined.append([last_token, token])
                            parenteses.append(0)
                        else:
                            fn_name.append([token])
                            parenteses.append(0)
                elif token[0] == tokenize.OP and token[1] == ".":
                    if fn_name[-1]:
                        fn_name[-1].append(token)
                    elif func_defined[-1]:
                        funcs_defined[-1].append(token)
                elif token[0] == tokenize.OP and token[1] == "(" and (fn_name or funcs_defined):
                    if fn_name[-1] or func_defined[-1]:
                        parenteses = map(lambda p:p+1,parenteses)
                        if parenteses[-1] == 1:
                            if func_defined[-1]:
                                funcs_defined[-1].append(token)
                            elif fn_name[-1]:
                                fn_name[-1].append(token)
                elif token[0] == tokenize.OP and token[1] == ")" and (fn_name or funcs_defined):
                    if fn_name[-1] or funcs_defined[-1]:
                        parenteses = map(lambda p:p-1,parenteses)
                        if parenteses[-1] == 0:
                            parenteses.pop()
                            if func_defined.pop():
                                funcs_defined[-1].append(token)
                            else:
                                fn_name[-1].append(token)
                                fn_names.append(fn_name.pop())
                elif fn_name[-1]:
                    if fn_name[-1][-1][0] != tokenize.OP or fn_name[-1][-1][1] not in ("(",")"):
                        if parenteses[-1] == 0 and token[1] != "=":
                            banned_words.append("".join(map(lambda f:f[1], filter(lambda f: f[1] not in ("(",")"), fn_name.pop()))))
                        elif parenteses[-1] == 0 and token[1] == "=":
                            func_locals.append("".join(map(lambda f:f[1], filter(lambda f: f[1] not in ("(",")"), fn_name.pop()))))
                        else:
                            fn_name.pop()
                        parenteses.pop()
                count += 1
                last_token = token
            if not fn_names and not first:
                break
            funcs_defined.pop(0)
            if not funcs_defined:
                raise Exception("Where's the function? o.O")
            if first:
                for fn in funcs_defined:
                    fn_name = "".join(map(lambda f:f[1], filter(lambda f: f[1] not in ("(",")", "def"), fn)))
                    logging.debug("Detectado definicao da funcao %s"%fn_name)
                    args = ["microthread", "microthread_locals", "microthread_globals", ""]
                    kwargs = []
                    commas = [-1,0,{"row":fn[-2][2][0]-1,"col":fn[-2][2][1],"space":True}]
                    parenteses = 1
                    for row in range(fn[1][2][0]-1, fn[-1][2][0]):
                        line = list(new_lines[row][:])
                        col_start  =  0
                        col_real_start = 0
                        col_end = len(line)
                        if row == fn[-2][2][0]-1:
                            col_real_start = fn[-2][2][1]+1
                            col_start = fn[1][2][1]
                        if row == fn[-1][2][0]-1:
                            col_end = fn[-1][2][1]
                        for col in range(col_real_start, col_end):
                            if line[col] == "(":
                                parenteses += 1
                            elif line[col] == ")":
                                parenteses -= 1
                            if line[col] == "," and parenteses == 1:
                                commas.append({"row":row,"col":col})
                                if commas[0] == -1:
                                    commas[1] += 1
                                    args.append("")
                                else:
                                    kwargs.append([""])
                            elif line[col] == "=" and parenteses == 1:
                                if commas[0] == -1:
                                    commas[0] = len(commas)-1
                                    kwargs.append([args.pop(),""])
                                else:
                                    kwargs[-1].append("")
                                continue
                            elif parenteses > 0:
                                if not kwargs:
                                    args[-1] += line[col]
                                else:
                                    kwargs[-1][-1] += line[col]
                        break
                    magic = filter(lambda arg: arg[0].startswith("*"), kwargs)
                    kwargs = filter(lambda arg: arg[1:], kwargs)
                    kwargs = map(lambda arg:[arg[0].strip(), arg[1]], kwargs)
                    args = filter(lambda arg:arg, map(lambda arg:arg.strip(), args))
                    if 'self' in args:
                        args.insert(0, args.pop(args.index("self")))
                    if not init:
                        init = "".join([new_lines[fn[0][2][0]][:fn[0][2][1]],tab])
                    s = ["def ",func_hash,"("]
                    s.extend(", ".join(args))
                    if kwargs:
                        s.extend(", ")
                        s.extend(",".join(map("=".join, kwargs)))
                    if magic:
                        s.extend(", ")
                        s.extend(",".join(magic))
                    s.extend("):\n")
                    if pyx_to_dll:
                        allargs_vars = map(lambda arg:arg[0], kwargs)+args+banned_words
                        vars_used = filter(lambda argvar: argvar not in allargs_vars and argvar, set(vars_used))
                        if vars_used: #If Cython..
                            s.extend(init)
                            s.extend("global ")
                            s.extend(", ".join(vars_used))
                            s.extend("\n")
                    s.extend(init)
                    s.extend("globals().update(microthread_globals)\n")
                    s.extend(init)
                    s.extend("locals().update(microthread_locals)\n")
                    s.extend(init)
                    s.extend("del microthread_globals\n")
                    s.extend(init)
                    s.extend("del microthread_locals")
                    #banned_words.extend(["globals","locals"])
                    for row in range(fn[0][2][0]-1, fn[-1][2][0]):
                        line = list(new_lines[row][:])
                        col_start  =  0
                        col_end = len(line)
                        s_modify = []
                        if row == fn[0][2][0]-1:
                            col_start = fn[0][2][1]
                        if row == fn[-1][2][0]-1:
                            col_end = fn[-1][3][1]+1
                            s_modify = s
                            s = []
                        if not s_modify:
                            s_modify = s[0:col_end-col_start]
                            s = s[col_end-col_start:]
                        to_modify[row] = to_modify.get(row, [])+[{
                                                                  "col": col_start,
                                                                  "end": col_end,
                                                                  "str":"".join(s_modify),
                                                                  "modify":True
                                                                  }]
                    first = False
                    break
            else:
                for fn in fn_names:
                    at_init = (len(new_lines[fn[0][2][0]-1])-len(new_lines[fn[0][2][0]-1].lstrip())) == fn[0][2][1] and new_lines[fn[-1][2][0]-1][fn[-1][2][1]+1:] == ""
                    fn_name = "".join(map(lambda f:f[1], filter(lambda f: f[1] not in ("(",")"), fn)))
                    logging.debug("Detectado funcao: %s"%fn_name)
                    args = [""]
                    kwargs = []
                    commas = [-1,0,{"row":fn[-2][2][0]-1,"col":fn[-2][2][1],"space":True}]
                    parenteses = 1
                    for row in range(fn[0][2][0]-1, fn[-1][2][0]):
                        line = list(new_lines[row][:])
                        col_start  =  0
                        col_real_start = 0
                        col_end = len(line)
                        if row == fn[-2][2][0]-1:
                            col_real_start = fn[-2][2][1]+1
                            col_start = fn[0][2][1]
                        if row == fn[-1][2][0]-1:
                            col_end = fn[-1][2][1]
                        for col in range(col_real_start, col_end):
                            if line[col] == "(":
                                parenteses += 1
                            elif line[col] == ")":
                                parenteses -= 1
                            if line[col] == "," and parenteses == 1:
                                commas.append({"row":row,"col":col})
                                if commas[0] == -1:
                                    commas[1] += 1
                                    args.append("")
                                else:
                                    kwargs.append([""])
                            elif line[col] == "=" and parenteses == 1:
                                if commas[0] == -1:
                                    commas[0] = len(commas)-1
                                    kwargs.append([args.pop(),""])
                                else:
                                    kwargs[-1].append("")
                                continue
                            elif parenteses > 0:
                                if not kwargs:
                                    args[-1] += line[col]
                                else:
                                    kwargs[-1][-1] += line[col]
                        break
                    kwargs = filter(lambda arg: arg[1:], kwargs)
                    kwargs = map(lambda arg:[arg[0].strip(), arg[1]], kwargs)
                    args = map(lambda arg:arg.strip(), args)
                    s =  [["(",""][at_init],"yield MicroThreadSignals.CALL_FUNCTION, ",fn_name,", ["]
                    more_args = filter(lambda arg: arg.startswith("*") and arg.count("*") == 1,[args, map(lambda arg:arg[0],kwargs)][kwargs != []])
                    more_kwargs = filter(lambda arg: arg.startswith("**") and arg.count("*") == 2,[args, map(lambda arg:arg[0],kwargs)][kwargs != []])
                    if more_kwargs:
                        more_kwargs = more_kwargs[0]
                        if kwargs != []:
                            kwargs.remove(more_kwargs)
                        else:
                            args.remove(more_kwargs)
                    else:
                        more_kwargs = ""
                    if more_args:
                        more_args = more_args[0]
                        if kwargs != []:
                            kwargs.remove(more_args)
                        else:
                            args.remove(more_args)
                    else:
                        more_args = ""
                    s.extend([", ".join(args),"]"])
                    if more_args:
                        s.extend(["+",more_args[1:]])
                    s.extend(", ")
                    s.extend([["dict(list(dict(",""][more_kwargs == ""],"{"])
                    s.extend(", ".join(map(lambda i: "".join(["'",i[0],"': ",i[1]]), kwargs)))
                    s.extend(["}",["".join([").items())+list(dict(",more_kwargs[2:],").items()))"]),""][more_kwargs==""],[")",""][at_init]])
                    for row in range(fn[0][2][0]-1, fn[-1][2][0]):
                        line = list(new_lines[row][:])
                        col_start  =  0
                        col_end = len(line)
                        s_modify = []
                        if row == fn[0][2][0]-1:
                            col_start = fn[0][2][1]
                        if row == fn[-1][2][0]-1:
                            col_end = fn[-1][3][1]
                            s_modify = s
                            s = []
                        if not s_modify:
                            s_modify = s[0:col_end-col_start]
                            s = s[col_end-col_start:]
                        to_modify[row] = to_modify.get(row, [])+[{
                                                                  "col": col_start,
                                                                  "end": col_end,
                                                                  "str":"".join(s_modify),
                                                                  "modify":True
                                                                  }]
                    break
            for line_number, changes in to_modify.iteritems():
                logging.debug("Atualizando linha %d"%line_number)
                line = list(new_lines[line_number])
                changes = sorted(changes,key=lambda l:l["col"])
                to_add = 0
                for change in changes:
                    if change.get("modify",False) and not change.get("end",False):
                        line[change["col"]+to_add] = change["str"]
                    elif change.get("modify",False) and change.get("end",False):
                        line[change["col"]+to_add:change["end"]+to_add] = change["str"]
                        to_add += len(change["str"])-((change["end"]+to_add)-(change["col"]+to_add))
                    else:
                        line.insert(change["col"]+to_add, change["str"])
                        to_add += 1
                logging.debug("Houve %d modificacoes na linha %d"%(to_add, line_number))
                new_lines[line_number] = "".join(line)
            new_lines = "\n".join(new_lines).split("\n")
        new_lines.append("".join([func_hash,".__name__ = '",func_name,"'"]))
        new_lines.append("".join([func_hash,".__doc__ = '",getattr(func, "__doc__",None) or "","'"]))
        if pyx_to_dll != None:
            new_lines.insert(0, "import cython")
        logging.info("Gerando nova funcao")
        MicroThreadPoll.codes[parseFuncs][func_hash] = "\n".join(new_lines)
        return MicroThreadPoll.codes[parseFuncs][func_hash] 
    @staticmethod
    def parseAndExecute(thread, parseFuncs = False, repeatCompile = 10, intervalCompile = 0.5):
        func_hash = MicroThreadPoll.getHash(thread)
        func = MicroThreadPoll.getFunction(thread)
        parseFuncs = getattr(func, "microThread_parseFuncs", parseFuncs)
        repeatCompile = getattr(func, "microThread_repeatCompile", repeatCompile)
        intervalCompile = getattr(func, "microThread_intervalCompile", intervalCompile)
        if MicroThreadPoll.funcs[parseFuncs].has_key(func_hash):
            logging.info("Retornando funcao cacheada")
            return MicroThreadPoll.funcs[parseFuncs][func_hash]
        if MicroThreadPoll.temp_dir:
            func_files = os.listdir(MicroThreadPoll.temp_dir)
            func_module_path = "_".join(func.__module__.split(".")+[func.__name__, md5(sys.version).hexdigest()])
            func_todelete = []
            for func_file in func_files:
                func_file = os.path.join(MicroThreadPoll.temp_dir, func_file)
                if func_module_path in func_file and func_hash not in func_file:
                    func_todelete.append(func_file)
            map(os.remove, func_todelete)
            func_module = "_".join([func_module_path,str(parseFuncs),func_hash])
            func_path = os.path.join(MicroThreadPoll.temp_dir, ".".join([func_module,"py"]))
            if not os.path.exists(func_path):
                code = MicroThreadPoll.parse(thread, parseFuncs)
                arq = open(func_path, "w+")
                arq.write(code)
                arq.close()
            func_module = __import__(func_module, {}, {}, [func_hash], 0)
            localVars = {}
            localVars[func_hash] =  getattr(func_module, func_hash)
            if pyx_to_dll and "<cyfunction" not in repr(localVars[func_hash]) and repeatCompile > 0:
                for _ in xrange(repeatCompile):
                    try:
                        pyx_to_dll(func_path, build_in_temp = True, inplace = True, reload_support=False)
                        func_module = reload(func_module)
                        break
                    except:
                        pass
                    time.sleep(intervalCompile)
                localVars[func_hash] = getattr(func_module, func_hash)
                localVars[func_hash].microThread_cythonPowered = "<cyfunction" in repr(localVars[func_hash])
            for func_file in func_files:
                func_file = os.path.join(MicroThreadPoll.temp_dir, func_file)
                if os.path.isdir(func_file) and "__pycache__" not in func_file:
                    func_todelete.append(func_file)
            map(shutil.rmtree, func_todelete)
            
        else:
            code = MicroThreadPoll.parse(thread, parseFuncs)
            logging.info("Compilando codigo")
            compiled_code = compile(code, "module.py", "exec")
            logging.info("Executando codigo")
            localVars = {}
            exec compiled_code in {},localVars
        if inspect.ismethod(func):
            localVars[func_hash] = types.MethodType(localVars[func_hash], func.im_self, func.im_class)
        #localVars[func_hash].__name__ = func_name
        #localVars[func_hash].__doc__ = func.__doc__
        logging.debug("Cacheando funcao")
        MicroThreadPoll.funcs[parseFuncs][func_hash] = localVars[func_hash]
        return localVars[func_hash] 
    @staticmethod
    def execute(thread, localVars, globalVars, args, kwargs):
        instance = MicroThreadTask(thread, thread.run_modified, localVars, globalVars, args, kwargs)
        MicroThreadPoll.add(instance)
        return instance
    def start(self):
        if not self.stopFlag:
            return
        poll = self
        def run():
            logging.debug("Iniciando Poll..")
            poll.stopFlag = False  
            getTask = MicroThreadPoll.tasks.get
            taskDone = MicroThreadPoll.tasks.task_done
            putTask = MicroThreadPoll.tasks.put_nowait
            n = 0
            while not poll.stopFlag:
                poll.suspendFlag.wait() #Wait if suspended
                task = getTask() #Get an task from the queue, blocking if needed
                if task in MicroThreadPoll.to_remove: #Detect if it's in the iterator
                    if n > 3:
                        MicroThreadPoll.to_remove = list(MicroThreadPoll.to_remove) #It need to be transformed in a list why::::It can slow the performance..=P    
                        n = 0
                    n += 1
                    MicroThreadPoll.to_remove = (a_task for a_task in MicroThreadPoll.to_remove if a_task !=task) #Generator Expressions <3
                    continue #If removed, this cannot be executed!
                taskDone() #If anyone need to know when the tasks terminated xD
                try:
                    task() #It's just the next method! 
                except StopIteration:
                    continue #'Remove' the item from the queue, just to not process this task in the next loop
                putTask(task) #Add the task to the end of the queue, to continue in a next loop
            poll.stopFlag = True
        if self.isThread():
            self.thread = threading.Thread(target=run)
            self.thread.daemon = True
            self.thread.start()
        elif self.thread is False:
            run()
    @staticmethod
    def getInstance(threaded=True):
        if not MicroThreadPoll.instance:
            MicroThreadPoll.temp_dir = "./cache/"
            sys.path.append(MicroThreadPoll.temp_dir)
            logging.info("Iniciando Polls")
            MicroThreadPoll.instance = []
            cpu_count = 1
            if threaded is True:
                if multiprocessing is not None:
                    try:
                        cpu_count = multiprocessing.cpu_count()
                    except NotImplementedError:
                        pass
                elif hasattr(os,"sysconf"):
                    try:
                        cpu_count = os.sysconf("SC_NPROCESSORS_CONF")
                    except ValueError:
                        pass
            elif threaded > 1:
                cpu_count = threaded
            logging.info("Abrindo %d %s"%(cpu_count,["polls","threads"][threaded is not False]))
            for _ in xrange(cpu_count):
                poll = MicroThreadPoll()
                poll.setThread(threaded is not False)
                MicroThreadPoll.instance.append(poll)
                MicroThreadPoll.size += 1
        if MicroThreadPoll.count >= MicroThreadPoll.size:
            MicroThreadPoll.count = 0
        result = MicroThreadPoll.instance[MicroThreadPoll.count]
        MicroThreadPoll.count += 1
        return result
    @staticmethod
    def getInstancesCount():
        return MicroThreadPoll.size
    @staticmethod 
    def getInstances():
        if not MicroThreadPoll.instance:
            MicroThreadPoll.getInstance()
        for instance in MicroThreadPoll.instance:
            yield instance
    @staticmethod
    def startAll():
        return map(MicroThreadPoll.start, MicroThreadPoll.getInstances())
    @staticmethod
    def stopAll():
        return map(MicroThreadPoll.stop, MicroThreadPoll.getInstances())
    @staticmethod
    def suspendAll():
        return map(MicroThreadPoll.suspend, MicroThreadPoll.getInstances())
    @staticmethod
    def resumeAll():
        return map(MicroThreadPoll.resume, MicroThreadPoll.getInstances())
class MicroThread(object):
    def __init__(self, *args, **kwargs):
        '''Initializes a new MicroThread'''
        logging.info("Criando nova micro-thread")
        if not args:
            args = list(args)
            args.append(self.run)
        if callable(kwargs.get("fn", args[0])):
            self.run = kwargs.get("fn", args[0])
            if kwargs.has_key("fn"):
                del kwargs["fn"]
        self.callbacks = {}
        for mode in MicroThreadCallbacksMode:
            self.callbacks[mode] = []
        if callable(kwargs.get("microThread_callback")):
            self.callbacks[MicroThreadCallbacksMode.ALL].append(kwargs.pop("microThread_callback"))
        self.parseFuncs = kwargs.pop("microThread_parseFuncs",True)
        self.repeatCompile = kwargs.pop("microThread_repeatCompile",10)
        self.intervalCompile = kwargs.pop("microThread_intervalCompile",0.1)
        self.localVars = {}
        self.localVars.update(locals().copy())
        self.globalVars = {}
        self.globalVars.update(globals().copy())
        self.globalVars.update(sys.modules)
        for n in range(0, 100):
            try:
                f = sys._getframe( n )
            except ValueError:
                break
            self.localVars.update(f.f_locals)
            self.globalVars.update(f.f_globals)
        self.globalVars.update({self.run.__name__: self.run})
        self.globalVars.update(self.run.func_globals)
        self.globalVars.update(getattr(self.run,"microThread_globals", {}))
        self.args = args[1:]
        self.kwArgs = kwargs
        self.run_modified = MicroThreadPoll.parseAndExecute(self, self.parseFuncs, self.repeatCompile, self.intervalCompile) #Parses, and executes, the code function, caching this in MicroThreadPoll.tempdir to allow compile with Cython, Jython and etc
        self.instance = None #It's not initiated after .start() call
        self.result = Queue.Queue() #A Queue to save the results from the MicroThread
    def isInPoll(self):
        return self.instance is not None
    def start(self):
        self.instance = MicroThreadPoll.execute(self, self.localVars, self.globalVars, self.args, self.kwArgs)
    def addCallback(self, fn, mode = MicroThreadCallbacksMode.ALL):
        self.callbacks[mode].append(fn)
    def setPriority(self, priority):
        if not self.isInPoll():
            raise Exception("Can't set priority with the process not running")
            return False
        self.instance.setPriority(priority)
        return True
    def setTimeout(self, timeout):
        if not self.isInPoll():
            raise Exception("Can't set timeout with the process not running")
            return False
        self.instance.setTimeout(timeout)
        return True
    def suspend(self):
        if not self.isInPoll():
            raise Exception("Can't suspend with the process not running")
            return False
        self.instance.suspend()
        return True
    def resume(self):
        if not self.isInPoll():
            raise Exception("Can't resume with the process not running")
            return False
        self.instance.resume()
        return True
    def kill(self):
        if not self.isInPoll():
            raise Exception("Can't kill with the process not running")
            return False
        self.instance.kill()
        return True
    def throw(self, type_exception, *args, **kwargs):
        if not self.isInPoll():
            raise Exception("Can't kill with the process not running")
            return False
        self.instance.throw(type_exception, *args, **kwargs)
    def getTimeRunning(self):
        if not self.isInPoll():
            raise Exception("Can't check this with the process not running")
            return False
        return self.instance.getTimeRunning()
    def isWaiting(self):
        if not self.isInPoll():
            raise Exception("Can't check this with the process not running")
            return False
        return self.instance.isWaiting()
    def isSuspended(self):
        if not self.isInPoll():
            raise Exception("Can't check this with the process not running")
            return False
        return self.instance.isSuspended()
    def isRunning(self):
        if not self.isInPoll():
            raise Exception("Can't check this with the process not running")
            return False
        return self.instance.isRunning()
    def send(self, val):
        if not self.isInPoll():
            raise Exception("Can't send a value with the process not running")
            return False
        return self.instance.send(val)
    def callCallback(self, mode, arg):
        if not arg[1:] and arg:
            arg = arg[0]
        elif not arg:
            arg = None
        for cb in self.callbacks[mode]:
            if getattr(cb, "microThread_enable", True):
                th = MicroThread(cb, self, mode, arg)
                th.start()
            else:
                cb(self, mode, arg)
        for cb in self.callbacks[MicroThreadCallbacksMode.ALL]:
            if getattr(cb, "microThread_enable", True):
                th = MicroThread(cb, self, mode, arg)
                th.start()
            else:
                cb(self, mode, arg)
    def isTerminated(self):
        return self.terminated.is_set()
    def join(self):
        if not self.isInPoll():
            raise Exception("Can't wait a microthread with the process not running")
            return False
        return self.instance.join()
    def waitResult(self, oldResult=False, send=False):
        if not self.isInPoll():
            raise Exception("Can't wait a microthread with the process not running")
            return False
        return self.instance.waitResult(oldResult, send)
#class OrderedPrint(MicroThread):
#    def __init__(self):
#        super(OrderedPrint, self).__init__(microThread_parseFuncs=False)
#        self.messages = Queue.Queue()
#        self.count = 0
#        self.stdout = sys.stdout
#        self.logger = _logging.getLogger("OrderedPrint")
#        self.lock = threading.Lock()
#    def write(self, msg):
#        self.lock.acquire()
#        self.logger.debug("Adicionando mensagem ao buffer...")
#        #self.messages.put_nowait(str(msg).strip())
#        self.stdout.write(msg)
#        self.lock.release()
#    def install(self):
#        self.logger.info("Instalando OrderedPrint..")
#        sys.stdout = self
#    def uninstall(self):
#        self.logger.info("Desinstalando OrderedPrint..")
#        sys.stdout = self.stdout
#    def join(self):
#        self.logger.debug("Aguardando termino das mensagens..")
#        self.messages.join()
#    def run(self):
#        while True:
#            try:
#                msg = self.messages.get_nowait()
#            except:
#                continue
#            if not msg:
#                continue
#            self.count += 1
#            self.stdout.write("".join([msg,"\n"]))
#            self.logger.debug("%d mensagens postadas"%self.count)
#            self.messages.task_done()
#    def getCount(self):
#        return self.count
#    @staticmethod
#    def getInstance():
#        if not hasattr(OrderedPrint,"instance"):
#            OrderedPrint.instance = OrderedPrint()
#            OrderedPrint.instance.start()
#        return OrderedPrint.instance
def microThreadParseFuncsDisable(fn):
    fn.microThread_parseFuncs = False
    return fn
class OrderedPrint:
    def __init__(self):
        self.lock = threading.Lock()
        self.logger = _logging.getLogger("OrderedPrint")
        self.stdout = sys.stdout
    @microThreadParseFuncsDisable
    def write(self, msg):
        #self.lock.acquire()
        self.logger.debug("Adicionando mensagem ao buffer...")
        #self.messages.put_nowait(str(msg).strip())
        self.stdout.write(msg)
        #self.lock.release()
    def install(self):
        self.logger.info("Instalando OrderedPrint..")
        sys.stdout = self
    def uninstall(self):
        self.logger.info("Desinstalando OrderedPrint..")
        sys.stdout = self.stdout
    @staticmethod
    def getInstance():
        if not hasattr(OrderedPrint,"instance"):
            OrderedPrint.instance = OrderedPrint()
            #OrderedPrint.instance.start()
        return OrderedPrint.instance

def microThreadDecorator(fn):
    def microThread(*args, **kwargs):
        if not kwargs.pop("microThread_enable", True):
            return fn(*args, **kwargs)
        async = kwargs.pop("microThread_async", True) #Defines if it's async..
        autoStart = kwargs.pop("microThread_autoStart", True)
        m = MicroThread(fn, *args, **kwargs) #Create a MicroThread..
        if async:
            if autoStart: #If it can auto-start!
                m.start()#It auto start!
            return m
        else:
            m.start() #Start if not async (it need to be started to await a result)
            return m.waitResult() #Await a result 
    microThread.__name__ = fn.__name__
    microThread.oldFunc = fn
    microThread.microThreadDecorated = True
    MicroThreadPoll.parse(fn, True) #Just a memory cache
    MicroThreadPoll.parse(fn, False) #Just a memory cache
    return microThread
        
