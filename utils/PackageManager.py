from utils.BasicClass import enum
import Queue, logging as _logging, urllib, urlparse, re, tarfile, subprocess, sys, os,shlex, platform, tempfile, shutil
import __builtin__
logging = _logging.getLogger("PackageManager")
class PackageActions(enum):
    INSTALL = None
    UPGRADE = None
    UNINSTALL = None
class Package:
    def __init__(self, name, indexName = None, action=None, version=None):
        self.name = name
        self.indexName = [name,indexName][indexName is not None]
        self.version = version
        self.action = action
    # Getters 
    def getName(self):
        return self.name
    def getIndexName(self):
        return self.indexName
    def getVersion(self):
        return self.version
    def getAction(self):
        return self.action
    
    # Setters 
    def setName(self, new_name):
        self.name = new_name
    def setIndexName(self, new_indexName):
        self.indexName = new_indexName
    def setVersion(self, new_version):
        self.version = new_version
    def setAction(self, new_action):
        self.action = new_action
    
    # setRow 
    def setRow(self, row):
        self.name = row['name']
        self.indexName = row['indexName']
        self.version = row['version']
        self.action = row['action']
    
    
    # toArray 
    def toArray(self):
        result={}
        result['name'] = self.name
        result['indexName'] = self.indexName
        result['version'] = self.version
        result['action'] = self.action
        return result
class PackagesManager(enum):
    EASY_INSTALL = None
    PIP = None

class PackageManager(object):
    @staticmethod
    def install():
        if platform.system() == "Linux" and os.getuid() != 0:
            logging.error("Execute o programa como root para manipular pacotes")
        PackageManager.availables = []
        if PackageManager.install_easy_install():
            PackageManager.availables.append(PackagesManager.EASY_INSTALL)
        if PackageManager.install_pip():
            PackageManager.availables.append(PackagesManager.PIP)
        if not PackageManager.availables:
            raise Exception("There none packages manager available")
        #PackageManager.availables.reverse()
        lista = map(lambda package_installer: [PackageManager.run_pip, PackageManager.run_easy_install][package_installer == PackagesManager.EASY_INSTALL], PackageManager.availables)
        @staticmethod
        def run(package):
            for installer in lista:
                result = installer(package)
                print result
                if result:
                    break
            return result
        PackageManager.run = run
        #Cleanup!
        PackageManager.run_easy_install = None
        PackageManager.install_easy_install = None
        PackageManager.run_pip = None
        PackageManager.install_pip = None
        PackageManager.install = None
    @staticmethod
    def addPackage(*args, **kwargs):
        package = Package(*args, **kwargs)
        package.setAction(PackageActions.INSTALL)#It's installing a package
        return PackageManager.run(package)#Add to queue
    @staticmethod
    def installPackage(*args, **kwargs):
        return PackageManager.addPackage(*args, **kwargs) #It's the same
    @staticmethod
    def upgradePackage(*args, **kwargs):
        package = Package(*args, **kwargs)
        package.setAction(PackageActions.UPGRADE)#It's upgrading a package
        return PackageManager.run(package)#Add to queue
    @staticmethod
    def removePackage(*args, **kwargs):
        package = Package(*args, **kwargs)
        package.setAction(PackageActions.UNINSTALL) #It's removing a package
        return PackageManager.run(package)#Add to queue
    @staticmethod
    def uninstallPackage(*args, **kwargs):
        return PackageManager.removePackage(*args, **kwargs)#It's the same
    @staticmethod
    def importPackage(*args, **kwargs):
        package = Package(*args, **kwargs)
        logging.info("Importando %s..."%package.getName())
        try:
            sys.modules.pop(package.getName(),None)
            n = __import__(package.getName())
        except ImportError:
            logging.debug("Instalando pacote %s.."%package.getName())
            package.setAction(PackageActions.INSTALL)
            if PackageManager.run(package):
                logging.debug("Tentando importatr novamente..")
                sys.modules.pop(package.getName(),None)
                n = __import__(package.getName())
            else:
                raise ImportError("Can't install %s"%package.getName())
        logging.debug("Botando no espaco global..")
        reg = dict([[package.getName(), n]])
        globals().update(reg.copy())
        locals().update(reg.copy())
        sys.modules.update(reg.copy())
        setattr(__builtin__, package.getName(), n)
        return n
    @staticmethod
    def getAvailable():
        return  PackageManager.availables
    @staticmethod
    def cleanup_easy_install():
        logging.info("Fazendo clean-up do Easy Install..")
        if PackageManager.setuptools_temp and os.path.exists(PackageManager.setuptools_temp):
            shutil.rmtree(PackageManager.setuptools_temp,True)
        logging.debug("Clean-up terminado! \o/")
        PackageManager.cleanup_easy_install = None
        PackageManager.setuptools_temp = None
    @staticmethod
    def install_easy_install():
        try:
            sys.modules.pop("setuptools",None)
            import setuptools
        except ImportError:
            logging.info("Instalando SetupTools..")
            u = "http://pypi.python.org/packages/source/s/setuptools/"
            logging.debug("Detectando ultima versao")
            handler = urllib.urlopen(u)
            logging.debug("Criando diretorio temporario..")
            PackageManager.setuptools_temp = tempfile.mkdtemp() #Get a temporary directory
            logging.debug("Diretorio temporario criado: %s"%PackageManager.setuptools_temp)
            logging.debug("Baixando SetupTools")
            try:
                urllib.urlretrieve(urlparse.urljoin(u, re.findall("<a href=\"(setuptools[^\"]*)\">", handler.read())[-1]), os.path.join(PackageManager.setuptools_temp ,"setuptools.tar.gz"))
            except Exception,e:
                logging.error("Houve uma falha durante o Download do arquivo: %s",e)
                return False
            logging.debug("Extraindo conteudo do arquivo")
            os.mkdir(os.path.join(PackageManager.setuptools_temp, "setuptools"))
            try:
                thandler = tarfile.open(os.path.join(PackageManager.setuptools_temp, "setuptools.tar.gz"))
                thandler.extractall( os.path.join(PackageManager.setuptools_temp,"setuptools"))
                logging.info("Detectando localizacao do arquivo setup.py")
                f = [f.name for f in thandler.getmembers() if "/setup.py" in f.name and f.name.count("/") == 1][0]
                logging.debug("Detectado >>> %s",f)
                thandler.close()
            except Exception,e:
                logging.error("Houve uma falha durante a extracao do arquivo %s",e)
                PackageManager.cleanup_easy_install()
                return False
            del thandler
            logging.debug("Executando arquivo setup.py")
            try:
                h = subprocess.Popen([sys.executable, os.path.join(PackageManager.setuptools_temp, "setuptools", f), "install"],shell=False, stdout=[subprocess.PIPE,sys.stdout][logging.isEnabledFor(_logging.DEBUG)])
                h.wait()
                del h
            except Exception,e:
                logging.error("Houve uma falha durante a execucao do arquivo: %s",e)
                PackageManager.cleanup_easy_install()
                return False
            logging.debug("Verificando instalacao")
            PackageManager.refresh_packages()
            try:
                import setuptools
            except ImportError:
                logging.error("Houve uma falha bem desconhecida durante a instalacao do SetupTools..:(")
                PackageManager.cleanup_easy_install()
                return False
            PackageManager.cleanup_easy_install()
        return True
    @staticmethod
    def cleanup_pip():
        logging.info("Fazendo clean-up do PIP..")
        if PackageManager.pip_temp and os.path.exists(PackageManager.pip_temp):
            shutil.rmtree(PackageManager.pip_temp, True)
        logging.debug("Clean-up terminado!")
        PackageManager.cleanup_pip = None
        PackageManager.pip_temp = None
    @staticmethod
    def install_pip():
        try:
            sys.modules.pop("pip",None)
            import pip
        except ImportError:
            try:
                logging.debug("Criando diretorio temporario..")
                PackageManager.pip_temp = tempfile.mkdtemp()
                logging.debug("Diretorio temporario criado: %s"%PackageManager.pip_temp)
                logging.info("Tentando instalar o PIP")
                logging.debug("Instalando o Distribute")
                urllib.urlretrieve("http://python-distribute.org/distribute_setup.py", os.path.join(PackageManager.pip_temp, "distribute_setup.py"))
                h = subprocess.Popen(" ".join([sys.executable, os.path.join(PackageManager.pip_temp, "distribute_setup.py")]),shell=True, stdout=[subprocess.PIPE,sys.stdout][logging.isEnabledFor(_logging.DEBUG)])
                h.wait()
                del h
                logging.debug("Instalando o PIP")
                urllib.urlretrieve("https://github.com/pypa/pip/raw/master/contrib/get-pip.py", os.path.join(PackageManager.pip_temp, "get_pip.py"))
                h = subprocess.Popen(" ".join([sys.executable, os.path.join(PackageManager.pip_temp, "get_pip.py")]),shell=True, stdout=[subprocess.PIPE,sys.stdout][logging.isEnabledFor(_logging.DEBUG)])
                h.wait()
                del h
                PackageManager.refresh_packages()     
                PackageManager.cleanup_pip()
                try:
                    import pip
                except ImportError:
                    return False
            except:
                logging.error("Ocorreu um erro durante a instalacao do PIP")
                return False
        return True       
    @staticmethod
    def refresh_packages():
        logging.info("Atualizando informacoes dos pacotes")
        path = sys.path[:]
        sys.path = []
        map(sys.path.append, path)
        for directory in path:
            logging.debug("Verificando %s"%directory)
            if not os.path.exists(directory):
                logging.debug("Removendo %s"%directory)
                sys.path.remove(directory)
                continue
            if not os.path.isdir(directory):
                continue
            files = os.listdir(directory)
            for f in files:
                f = os.path.join(directory, f)
                if f.endswith(".egg") and f not in sys.path:
                    logging.debug("Adicionando novo pacote %s"%f)
                    sys.path.append(f)
    @staticmethod
    def run_easy_install(package):
        args = {}
        if package.getVersion():
            version = str(package.getVersion())
            modify = version[0] not in ("=",">","<")
            args[PackageActions.INSTALL] = "".join([package.getIndexName(),["","=="][modify],version])#Install a Package
            args[PackageActions.UPGRADE] = args[PackageActions.INSTALL]#Upgrades a package (is the same syntax with a version)
        else:
            args[PackageActions.INSTALL] = package.getIndexName()#Install a Package
            args[PackageActions.UPGRADE] = " ".join(["--upgrade",package.getIndexName()])#Upgrades a package 
        args[PackageActions.UNINSTALL] = " ".join(["-mxN",package.getIndexName()])#Uninstall a Package
        modes = {
                 PackageActions.INSTALL:"Instalando",
                 PackageActions.UPGRADE:"Atualizando",
                 PackageActions.UNINSTALL:"Desinstalando"
        }
        easy_install_args = shlex.split(" ".join(["easy_install"]+args[package.getAction()].split(" ")))
        logging.info("%s %s via Easy Install com os argumentos %s"%(modes[package.getAction()],package.getName(), " ".join(easy_install_args)))
        try: 
            h = subprocess.Popen(easy_install_args,shell=False,stdout=[subprocess.PIPE,sys.stdout][logging.isEnabledFor(_logging.DEBUG)])
            logging.debug("Aguardando termino da instalacao..")
            h.wait()
            del h
        except Exception,e:
            modes = {
                     PackageActions.INSTALL:"Instalacao",
                     PackageActions.UPGRADE:"Atualizacao",
                     PackageActions.UNINSTALL:"Desinstalacao"
            }
            logging.error("Houve um erro durante a %s do modulo: %s com os argumentos %s"%(modes[package.getAction()],e," ".join(easy_install_args)))
            pass
        PackageManager.refresh_packages()
        try:
            logging.info("Importando %s"%package.getName())
            reload(__import__(package.getName()))
        except ImportError, e:
            logging.debug("Ocorreu um erro durante a importacao...Modulo nao encontrado")
            return package.getAction() == PackageActions.UNINSTALL
        logging.info("Importacao realizada com sucesso")
        return package.getAction() != PackageActions.UNINSTALL
    @staticmethod
    def run_pip(package):
        args = {}
        if package.getVersion():
            version = str(package.getVersion())
            modify = version[0] not in ("=",">","<")
            args[PackageActions.INSTALL] = "".join(["install ",package.getIndexName(),["","=="][modify],version])#Install a Package
            args[PackageActions.UPGRADE] = args[PackageActions.INSTALL]#Upgrades a package (is the same syntax with a version)
        else:
            args[PackageActions.INSTALL] = " ".join(["install",package.getIndexName()])#Install a Package
            args[PackageActions.UPGRADE] = " ".join(["install --upgrade",package.getIndexName()])#Upgrades a package 
        args[PackageActions.UNINSTALL] = " ".join(["uninstall -y",package.getIndexName()])#Uninstall a Package
        pip_args = shlex.split(" ".join(["pip"]+args[package.getAction()].split(" ")))
        modes = {
                 PackageActions.INSTALL:"Instalando",
                 PackageActions.UPGRADE:"Atualizando",
                 PackageActions.UNINSTALL:"Desinstalando"
        }
        logging.info("%s modulo %s via PIP com os argumentos %s"%(modes[package.getAction()],package.getName()," ".join(pip_args)))
        try:
            
            h = subprocess.Popen(pip_args,shell=False, stdout=[subprocess.PIPE,sys.stdout][logging.isEnabledFor(_logging.DEBUG)])
            h.wait()
            del h
        except Exception,e:
            modes = {
                     PackageActions.INSTALL:"Instalacao",
                     PackageActions.UPGRADE:"Atualizacao",
                     PackageActions.UNINSTALL:"Desinstalacao"
            }
            logging.error("Ops, houve um erro durante a %s do modulo %s com os argumentos %s"%(modes[package.getAction()],e," ".join(pip_args)))
            pass
        PackageManager.refresh_packages()
        try:
            logging.info("Importando %s",package.getName())
            reload(__import__(package.getName()))
        except ImportError, e:
            logging.debug("Ocorreu um erro durante a importacao...Modulo nao encontrado")
            return package.getAction() == PackageActions.UNINSTALL
        logging.info("Importacao realizada com sucesso")
        return package.getAction() != PackageActions.UNINSTALL
PackageManager.install()
