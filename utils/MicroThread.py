import inspect, tokenize, itertools, threading, string, random, sys, os, time, re, logging as _logging, Queue
try:
    from hashlib import md5
except ImportError:
    from md5 import md5    
try:
    import multiprocessing
except ImportError:
    multiprocessing = None
try:
    from functools import partial
except ImportError:
    def partial(func, *args, **keywords):
        def newfunc(*fargs, **fkeywords):
            newkeywords = keywords.copy()
            newkeywords.update(fkeywords)
            return func(*(args + fargs), **newkeywords)
        newfunc.func = func
        newfunc.args = args
        newfunc.keywords = keywords
        newfunc.__name__ = func.__name__
        return newfunc
logging = _logging.getLogger("MicroThread")
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
        if mode == "yield":
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
        elif mode == "return":
            self.endFlag = True
class MicroThreadTask(object):
    def __init__(self, thread, fn, *args, **kwargs):
        self.thread = thread
        self.task = fn(*args, **kwargs)
        self.timeout = None
        self.suspended = False
        self.killed = False
        self.time_processing = 0
        self.priority = 100
        self.count = 0
        self.to_send = Queue.Queue()
        self.need_send = False
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
        self.thread.getPoll().tasks.remove(self)
    def send(self,msg):
        logging.debug("Adicionando informacao ao queue para envio posterior")
        self.to_send.put(msg)
        self.resume()
    def resume(self):
        if not self.suspended:
            return
        logging.debug("Resumindo tarefa")
        self.suspended = False
        self.thread.getPoll().tasks.add(self)
    def isSuspended(self):
        return self.suspended
    def kill(self):
        self.killed = True
    def throw(self, type_exception, *args, **kwargs):
        logging.debug("Criando excecao no generator")
        self.task.throw(type_exception, *args, **kwargs)
    def isWaiting(self):
        return self.need_send
    def next(self):
        while self.count > 100:
            init_time = time.time()
            try:
                if self.need_send:
                    logging.debug("Aguardando informacao")
                    try:
                        m = self.to_send.get_nowait()
                    except:
                        self.count -= 100
                        continue
                    logging.debug("Enviando informacao")
                    result = self.task.send(m)
                    self.to_send.task_done()
                    self.need_send = False
                else:
                    result = self.task.next()
            except StopIteration:
                result = [1]
            final_time = time.time()
            self.time_processing += final_time - init_time
            if self.killed:
                logging.debug("Matando tarefa")
                self.thread.callCallback("killed", [])
                try:
                    self.task.close()
                except GeneratorExit:
                    pass
                raise StopIteration()
                break
            elif self.timeout != None and self.timeout < self.time_processing:
                logging.debug("Retornando timeout")
                self.thread.callCallback("timeout", [])
                try:
                    self.task.close()
                except GeneratorExit:
                    pass
                raise StopIteration()
                break
            if result[0] == 1:
                logging.debug("Retornando resultado da tarefa")
                self.thread.callCallback("return", result[1:])
                try:
                    self.task.close()
                except:
                    pass
                raise StopIteration()
                break
            elif result[0] in (2,3):
                logging.debug("Retornando yield")
                self.need_send = result[0] == 3
                self.thread.callCallback("yield", result[1:])
                if self.need_send:
                    logging.debug("Aguardando resultado")
                    self.suspend()
            elif result[0] == 4:
                logging.debug("Chamando funcao %s"%result[1].__name__)
                self.need_send = True
                if result[3].get("microthread_enable",True):
                    if result[3].has_key("microthread_enable"):
                        del result[3]["microthread_enable"]
                    try:
                        mt = MicroThread(result[1], *result[2],**result[3])
                    except:
                        try:
                            self.send(result[1](*result[2],**result[3]))
                        except Exception, e:
                            self.throw(type(e), e.message)
                        mt = None
                    if mt:
                        self.suspend()
                        mt.start()
                        if inspect.isgeneratorfunction(result[1]):
                            SimpleGenerator(self.thread, mt)
                        else:
                            def returnCallback(self, thread, mode, result):
                                if mode == "return":
                                    logging.debug("Retornando chamada da funcao")
                                    self.send(result)
                                    self.resume()
                            returnCallback.im_self = self
                            mt.addCallback(returnCallback)
                else:
                    try:
                        self.send(result[1](*result[2],**result[3]))
                    except Exception, e:
                        self.throw(type(e), e.message)
            self.count -= 100 
        self.count += self.priority
    def getThread(self):
        return self.thread
    def getPriority(self):
        return self.priority
    def getTimeout(self):
        return self.timeout
    def getTask(self):
        return self.task
class MicroThreadTasks:
    def __init__(self):
        self.tasks = []
        self.counter = 0
        self.size = 0
        self.to_add = Queue.Queue()
        self.to_remove = Queue.Queue()
    def add(self, task):
        logging.info("Adicionando nova tarefa")
        self.to_add.put_nowait(task)
    def remove(self, task):
        logging.info("Removendo tarefa")
        self.to_remove.put_nowait(task)
    def getSize(self):
        return self.size
    def __iter__(self):
        return self
    def next(self):
        while True:
            try:
                task = self.to_add.get_nowait()
            except Queue.Empty:
                break
            self.tasks.append(task)
            self.size += 1
            self.to_add.task_done()
        while True:
            try:
                task = self.to_remove.get_nowait()
            except Queue.Empty:
                break
            self.tasks.remove(task)
            self.size -= 1
            self.counter -= 1
            self.to_remove.task_done()
        if self.size == 0:
            raise StopIteration()
        if self.counter >= self.size or self.counter <= 0:
            self.counter = 0
        result = self.tasks[self.counter]
        self.counter += 1
        return result 
    def empty(self):
        return self.size == 0
class MicroThreadPoll:
    instance = None
    size = 0
    count = 0
    funcs = {}
    codes = {}
    def __init__(self):
        self.thread = False
        self.tasks = MicroThreadTasks()
        self.stopFlag = True
        self.suspendFlag = False
    def suspend(self):
        self.suspendFlag = True
    def stop(self):
        self.stopFlag = True
    def resume(self):
        self.suspendFlag = False
    def isRunning(self):
        return not self.stopFlag and not self.sleepFlag
    def setThread(self, thread):
        self.thread = thread
    def isThread(self):
        return self.thread is True
    def getTasks(self):
        return self.tasks
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
        for char in func_hash[:]:
            if char.isdigit():
                func_hash.append(func_hash.pop(0))
            else:
                break
        return "".join(func_hash)
    @staticmethod
    def parse(thread, parseFuncs = True):
        func = MicroThreadPoll.getFunction(thread)
        if inspect.isbuiltin(func):
            raise TypeError("Can't manipulate builtins code")
        else:
            code = inspect.getsource(func)
        func_hash = MicroThreadPoll.getHash(thread)
        logging.debug("Parseando funcao")
        opened = True
        lines = code.strip().split("\n")
        is_method = code.startswith("\t") or code.startswith(" "*4)
        lines = filter(lambda line: line != "@microThreadDecorator", lines)
        func_name = filter(lambda line: "def" in line, lines)[0].split("def ", 1)[1].split("(", 1)[0] 
        logging.debug("O nome da funcao e %s" % func_name)
        new_lines = []
        temp_code = []
        tab = ["    ", "\t"][code.count("\t") > 0]
        dont_work = False
        for line in lines:
            logging.debug("Processando nova linha")
            returnSome = False
            yieldSome = False
            dont_work = False
            if is_method and line[:len(tab)] == tab:
                line = line[len(tab):]
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
                    if token[1] == "return":
                        logging.debug("Statement return detectado")
                        returnSome = token
                    elif token[1] == "yield":
                        logging.debug("Statement yield detectado")
                        yieldSome = token
                    continue
                opened = False
            except:
                logging.debug("Linha nao-terminada, pulando...")
                opened = True
            if returnSome:
                logging.debug("Substituindo return")
                line = list(line)
                line[returnSome[2][1]:returnSome[3][1]] = "yield 1,"
                line = "".join(line) 
            elif yieldSome:
                logging.debug("Substituindo yield")
                line = list(line)
                line[yieldSome[2][1]:yieldSome[3][1]] = "yield "+["2","3"][line[yieldSome[2][1]-1]=="("]+","
                line = "".join(line) 
            if not opened and not temp_code[1:] and not dont_work:
                logging.debug("Atualizando funcao...")
                new_lines.append((line.count(tab) * tab) + "yield 0,")
            if not opened: 
                dont_work = False
            logging.debug("Adicionando nova linha")
            new_lines.append(line)
        #func_name = fn_names[0][0]
        #fn_names.reverse()
        
        while parseFuncs:
            tokens = list(tokenize.generate_tokens(iter(new_lines).next))
            to_modify = {}
            parenteses = [0]
            fn_name = [None]
            fn_names = []
            banned_words = ["yield","return","def","dict","items",func_name]
            count = 0
            func_locals = []
            for token in tokens:
                if fn_name[-1] and token[0] == tokenize.NAME and token[1] not in banned_words and parenteses[-1] == 0:
                    fn_name[-1].append(token)
                elif token[0] == tokenize.NAME and token[1] not in banned_words:
                    is_fn = False
                    dot = False
                    for temp_token in tokens[count+1:]:
                        if temp_token[0] == tokenize.OP:
                            if temp_token[1] == ".":
                                dot = True
                                continue
                            elif temp_token[1] == "(":
                                is_fn = True
                            else:
                                break
                        elif temp_token[0] == tokenize.NAME and dot:
                            continue
                        else:
                            break
                    if is_fn:
                        fn_name.append([token])
                        parenteses.append(0)
                elif fn_name[-1] and token[0] == tokenize.OP and token[1] == ".":
                    fn_name[-1].append(token)
                elif fn_name[-1] and token[0] == tokenize.OP and token[1] == "(":
                    parenteses = map(lambda p:p+1,parenteses)
                    if parenteses[-1] == 1:
                        fn_name[-1].append(token)
                elif fn_name[-1] and token[0] == tokenize.OP and token[1] == ")":
                    parenteses = map(lambda p:p-1,parenteses)
                    if parenteses[-1] == 0:
                        fn_name[-1].append(token)
                        fn_names.append(fn_name.pop())
                        parenteses.pop()
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
            if not fn_names:
                break
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
                s =  [["(",""][at_init],"yield ",["4","5"][at_init],", ",fn_name,", ["]
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
            print "\n".join(new_lines)
        logging.info("Gerando nova funcao")
        code = "\n".join(new_lines).replace("def " + func_name, "def " + func_hash)
        return code
    @staticmethod
    def parseAndExecute(thread, localVars, globalVars, parseFuncs = False):
        func_hash = MicroThreadPoll.getHash(thread)
        if MicroThreadPoll.funcs.has_key(func_hash):
            logging.info("Retornando funcao cacheada")
            return MicroThreadPoll.funcs[func_hash]
        func = MicroThreadPoll.getFunction(thread)
        func_name = func.__name__
        code = MicroThreadPoll.parse(thread, parseFuncs)
        logging.info("Compilando codigo")
        compiled_code = compile(code, "module.py", "exec")
        logging.info("Executando codigo")
        exec compiled_code in globalVars, localVars
        if func_name == "run":
            logging.debug("Adaptando funcao para self")
            localVars[func_hash] = partial(localVars[func_hash], thread)
        elif hasattr(func, "im_self"):
            localVars[func_hash] = partial(localVars[func_hash], func.im_self)
        logging.debug("Cacheando funcao")
        MicroThreadPoll.funcs[func_hash] = localVars[func_hash]
        return MicroThreadPoll.funcs[func_hash] 
    def execute(self, thread, args, kwargs):
        instance = MicroThreadTask(thread, thread.run_modified, *args, **kwargs)
        self.tasks.add(instance)
        return instance
    def start(self):
        poll = self
        def run():
            poll.stopFlag = False
            tasks = iter(poll.tasks)
            interval = 1 / float(sys.maxint)
            while not poll.stopFlag:
                if poll.suspendFlag:
                    logging.debug("Poll suspenso")
                    continue
                for task in tasks:
                    if task.isSuspended():
                        continue
                    time.sleep(interval)
                    try:
                        task.next()
                    except StopIteration:
                        tasks.remove(task)
                        continue
            poll.stopFlag = True
        if not self.stopFlag:
            return
        if self.isThread():
            self.thread = threading.Thread(target=run)
            self.thread.setDaemon(True)
            self.thread.start()
        elif self.thread is False:
            run()
    @staticmethod
    def getInstance(threaded=True):
        if not MicroThreadPoll.instance:
            logging.info("Iniciando Polls")
            MicroThreadPoll.instance = []
            cpu_count = 1
            if threaded is True:
                if multiprocessing is not None:
                    try:
                        cpu_count = multiprocessing.cpu_count()
                    except NotImplementedError:
                        pass
                else:
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
        logging.info("Criando nova micro-thread")
        if not args:
            args = list(args)
            args.append(self.run)
        if callable(kwargs.get("fn", args[0])):
            self.run = kwargs.get("fn", args[0])
            if kwargs.has_key("fn"):
                del kwargs["fn"]
        self.callback = []
        if callable(kwargs.get("microthread_callback")):
            self.callback.append(kwargs.get("microthread_callback"))
            del kwargs["microthread_callback"]
        self.poll = MicroThreadPoll.getInstance()
        self.parseFuncs = kwargs.get("microthread_parseFuncs",True)
        if kwargs.has_key("microthread_parseFuncs"):
            del kwargs["microthread_parseFuncs"]
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
            self.globalVars.update(f.f_locals)
            self.globalVars.update(f.f_globals)
        self.globalVars.update({self.run.__name__: self.run})
        self.globalVars.update(self.run.func_globals)
        self.args = args[1:]
        self.kwArgs = kwargs
        self.run_modified = self.poll.parseAndExecute(self, self.localVars, self.globalVars, self.parseFuncs)
        self.instance = None
    def setPoll(self, poll):
        self.poll = poll
    def getPoll(self):
        return self.poll
    def running(self):
        return self.instance is not None
    def start(self):
        self.instance = self.poll.execute(self, self.args, self.kwArgs)
    def addCallback(self, fn):
        self.callback.append(fn)
    def setPriority(self, priority):
        if not self.running():
            raise Exception("Can't set priority with the process not running")
            return False
        self.instance.setPriority(priority)
        return True
    def setTimeout(self, timeout):
        if not self.running():
            raise Exception("Can't set timeout with the process not running")
            return False
        self.instance.setTimeout(timeout)
        return True
    def suspend(self):
        if not self.running():
            raise Exception("Can't suspend with the process not running")
            return False
        self.instance.suspend()
        return True
    def resume(self):
        if not self.running():
            raise Exception("Can't resume with the process not running")
            return False
        self.instance.resume()
        return True
    def kill(self):
        if not self.running():
            raise Exception("Can't kill with the process not running")
            return False
        self.instance.kill()
        return True
    def throw(self, type_exception, *args, **kwargs):
        if not self.running():
            raise Exception("Can't kill with the process not running")
            return False
        self.instance.throw(type_exception, *args, **kwargs)
    def callCallback(self, mode, arg):
        if not self.callback:
            return
        for cb in self.callback:
            th = MicroThread(cb, self, mode, arg)
            th.start()
            #cb(self, mode, *args)
class OrderedPrint(MicroThread, object):
    def __init__(self):
        super(OrderedPrint, self).__init__(microthread_parseFuncs=False)
        self.messages = Queue.Queue()
        self.count = 0
        self.stdout = sys.stdout
    def write(self, msg):
        self.stdout.write(msg)
        #self.messages.put(msg)
    def install(self):
        sys.stdout = self
    def uninstall(self):
        sys.stdout = self.stdout
    def join(self):
        self.messages.join()
    def run(self):
        while True:
            try:
                msg = self.messages.get_nowait()
            except:
                continue
            self.count += 1
            self.stdout.write(str(msg))
            self.messages.task_done()
    def getCount(self):
        return self.count
    @staticmethod
    def getInstance():
        if not hasattr(OrderedPrint,"instance"):
            OrderedPrint.instance = OrderedPrint()
            OrderedPrint.instance.start()
            print "Iniciando OrderedPrint"
        return OrderedPrint.instance
def microThreadDecorator(fn):
    def microThread(*args, **kwargs):
        if not kwargs.get("micro_thread_enable", True):
            del kwargs["micro_thread_enable"]
            return fn(*args, **kwargs)
        m = MicroThread(fn, *args, **kwargs)
        m.start()
        return m
    microThread.__name__ = fn.__name__
    microThread.oldFunc = fn
    return microThread
        
