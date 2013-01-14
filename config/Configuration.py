import ConfigParser, os
from db.ActiveRecord import ActiveRecord
from utils import functools
class ConfigurationOption(ActiveRecord):
    def __init__(self, section, *args):
        self.section = section
        if args:
            self.key = args[0]
            if args[1:]:
                self.setValue(args[1])
    #Actions
    def load(self):
        if not self.section:
            raise Exception("Set a section to this option")
        if not self.section.getConfigFile().has_option(self.getSection().getName(), self.key):
            raise Exception("Cannot load a record that's not exists")
        else:
            self.setValue(self.section.getConfigFile().get(self.getSection().getName(), self.key))
    def insert(self):
        if not self.section:
            raise Exception("Set a section to this option")
        if self.section.getConfigFile().has_option(self.getSection().getName(), self.key):
            raise Exception("Cannot insert a record that's be saved")
        else:
            self.section.getConfigFile().set(self.getSection().getName(), self.key, self.value)
    def update(self):
        if not self.section:
            raise Exception("Set a section to this option")
        if not self.section.getConfigFile().has_option(self.getSection().getName(), self.key):
            raise Exception("Cannot update a record that's not exist")
        else:
            self.section.getConfigFile().set(self.getSection().getName(), self.key, self.value)
    def delete(self):
        if not self.section:
            raise Exception("Set a section to this option")
        if not self.section.getConfigFile().has_option(self.getSection().getName(), self.key):
            raise Exception("Cannot delete a record that's not exist")
        else:
            self.section.getConfigFile().remove_option(self.getSection().getName(), self.key)
    # Getters 
    def getSection(self):
        return self.section
    def getKey(self):
        return self.key
    def getValue(self):
        return self.value
    
    # Setters 
    def setSection(self, new_section):
        self.section = new_section
    def setKey(self, new_key):
        self.key = new_key
    def setValue(self, new_value):
        try:
            self.value = eval(new_value,{"__builtins__":None,"False":False,"True":True},{}) #Safely execute
        except:
            #If it's just a String
            self.value = new_value
    
    # setRow 
    def setRow(self, row):
        self.section = row['section']
        self.key = row['key']
        self.value = row['value']
    
    
    # toArray 
    def toArray(self):
        result={}
        result['section'] = self.section
        result['key'] = self.key
        result['value'] = self.value
        return result
    def toDict(self):
        return {
                "key":self.key,
                "value":self.value
        }
class ConfigurationSection(ActiveRecord):
    def __init__(self, configfile=None, name=None, parent=None):
        self.configfile = configfile
        self.parent = parent
        self.name = name
        self.options = []
        self.old_name = name
        self.sections = []
        self.files = []
    def load(self):
        self.options = [] 
        for option_name, option_value in self.configfile.items(self.name):
            option = ConfigurationOption(self, option_name, option_value)
            self.options.append(option)
            if option.getKey() == "include":
                values = option.getValue()
                if isinstance(values, basestring):
                    values = [values]
                for value in values:
                    inherit = value.split("#no_inherit")
                    value = inherit[0]
                    inherit = inherit[1:] == []
                    configfile = Configuration.getInstance().load(value, [None, self][inherit])
                    if inherit:
                        self.sections.extend(configfile.getSections())
                        self.files.append(configfile)
    def insert(self):
        try:
            self.configfile.add_section(self.name)
            map(ConfigurationOption.insert, self.options)
            return True
        except:
            return False
    def update(self):
        try:
            self.configfile.remove_section(self.old_name)
            self.insert()
        except:
            pass
    def delete(self):
        map(ConfigurationOption.delete, self.options)
        self.configfile.remove_section(self.name)
    # Getters 
    def getConfigFile(self):
        return self.configfile
    def getParent(self):
        return self.parent
    def getName(self):
        return self.name
    def getOption(self, name, default=None):
        for option in self.options:
            if option.getKey() == name:
                return option
        if default:
            return default
        raise Exception("Option not encountered")
    def hasOption(self, name):
        for option in self.options:
            if option.getKey() == name:
                return True
        return False
    # Setters 
    def setParent(self, new_parent):
        self.parent = new_parent
    def setName(self, new_name):
        if not self.old_name:
            self.old_name = new_name
        self.name = new_name
    # setRow 
    def setRow(self, row):
        self.parent = row['parent']
        self.name = row['name']
    
    # toArray 
    def toArray(self):
        result={}
        result['parent'] = self.parent
        result['name'] = self.name
        return result
    
    def _getMultipleOption(self, name):
        for section in self.sections:
            option = section.getOption(name)
            if option:
                yield option
    def _getSimpleOption(self, name):
        for section in self.sections:
            option = section.getOption(name)
            if option:
                return option
    def getSection(self, name):
        for section in self.sections:
            if section.getName() == name:
                return section
    def hasSection(self, name):
        for section in self.sections:
            if section.getName() == name:
                return True
        return False
    def getOptions(self):
        return self.options
    def getSections(self):
        return self.sections
    def toDict(self, include_options = True, include_sections = True, raw_values=False):
        result = {}
        if include_options:
            opts = {}
            if raw_values:
                for opt in self.options:
                    opts[opt.getKey()] = opt.getValue()
            else:
                for opt in self.options:
                    opts[opt.getKey()] = opt
            result["options"] = opts
        if include_sections:
            sects = {}
            if raw_values:
                for section in self.sections:
                    sects[section.getName()] = section.toDict(include_options, include_sections, raw_values)
            else:
                for section in self.sections:
                    sects[section.getName()] = section
            result["sections"]  = sects
        if include_options and include_sections:
            return result
        if not result:
            return result
        return result[["options","sections"][include_sections]]
class ConfigurationFile(ConfigParser.ConfigParser):
    def __init__(self, filename, section=None):
        ConfigParser.ConfigParser.__init__(self)
        self.sections = []
        self.section = section
        if not isinstance(filename, str):
            raise Exception("Invalid Filename")
        result = self.read(filename)
        if not result:
            raise Exception("File don't loaded")
        for section in self._sections:
            sect = ConfigurationSection(self, section)
            sect.load()
            if not self.section: 
                if Configuration.getInstance().hasSection(section):
                    raise Exception("Sections collide!")
                Configuration.getInstance().addSection(sect)
            self.sections.append(sect)
    def _getMultipleOption(self, name):
        for section in self.sections:
            option = section.getOption(name)
            if option:
                yield option
    def _getSimpleOption(self, name):
        for section in self.sections:
            option = section.getOption(name)
            if option:
                return option
    def getOption(self, name, multiple=False):
        if multiple:
            return self._getMultipleOption(name)
        else:
            return self._getSimpleOption(name)
    def hasOption(self, name):
        for section in self.sections:
            if section.hasOption(name):
                return True
        return False
    def hasSection(self, name):
        for section in self.sections:
            if section.getName() == name:
                return True
        return False
    def getSection(self, name, add=True):
        for section in self.sections:
            if section.getName() == name:
                return section
        if add:
            sect = ConfigurationSection(self, name)
            self.sections.append(sect)
            return sect
        else:
            raise ConfigParser.NoSectionError("No section detected")
    def getSections(self):
        return self.sections
    def save(self, filename):
        map(ConfigurationSection.update, self.sections)
        arq = open(filename, "w+")
        self._config.write(arq)
        arq.close()
    def toDict(self, include_options=True, include_subcategories=True, raw_values = False):
        result = {}
        if raw_values:
            for sect in self.sections:
                result[sect.getName()] = sect.toDict(include_options, include_subcategories, raw_values)
        else:
            for sect in self.sections:
                result[sect.getName()] = sect
        return result
class Configuration:
    def __init__(self):
        self.files = {}
        self.sections = {}
        self.sections_name = []
        def replaceConstructor():
            raise NotImplementedError("Call Configuration.getInstance() instead")
        Configuration.__init__ = replaceConstructor
    def addSection(self, section):
        self.sections[section.getName()] = section
    def hasSection(self, section):
        return self.sections.has_key(section)
    def getSection(self, section):
        return self.sections[section]
    def getSections(self):
        return self.sections
    def getOption(self, name, section=None):
        if not section:
            for sect in self.sections.itervalues():
                if sect.hasOption(name):
                    return sect.getOption(name)
        else:
            return self.sections[name].getOption(name)
    def hasOption(self, name, section=None):
        if not section:
            for sect in self.sections.itervalues():
                if sect.hasOption(name):
                    return True
            return False
        else:
            return self.sections[name].hasOption(name)
    def getFile(self, filename):
        filename = os.path.realpath(os.path.join(os.getcwd(), filename))
        return self.files[filename]
    def load(self, filename, section=None):
        filename = os.path.realpath(os.path.join(os.getcwd(), filename))
        if not self.files.has_key(filename):
            self.files[filename] = ConfigurationFile(filename, section)
        return self.files[filename] 
    def getPath(self, path="", default = None, original_parent=None):
        path = path.split("/")
        if not original_parent:
            original_parent = None
        parent = original_parent
        for item in path:
            if parent.hasSection(item):
                parent = parent.getSection(item)
            elif parent.hasOption(item):
                parent = parent.getOption(item)
                return parent
            else:
                return None
        if parent == original_parent:
            return None
        if default:
            if not isinstance(parent, ConfigurationOption):
                return default
            else:
                return parent.getValue()
        return parent
    @staticmethod
    def getInstance():
        if not hasattr(Configuration, "instance"):
            Configuration.instance = Configuration()
        return Configuration.instance
Configuration.getInstance()