'''
Created on 08/01/2013

@author: fernando
'''
from utils.BasicClass.enum import enum
import urllib, operator, Cookie
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
def convertToList(dictionary):
    is_list = True  # Indicates if can be a list
    for key, val in dictionary.iteritems():
        if isinstance(val, dict):  # It's a dictionary!
            dictionary[key] = convertToList(val)  # Recurse it!
        if not key.isdigit() and key:  # Verify if it's not a number
            is_list = False  # It can't be a list..
    if is_list and dictionary:  # It have keys and it's a list?
        keys = sorted([[int(item[0]), item[1]] for item in dictionary.iteritems()], key=operator.itemgetter(0))
        numbers = [number[0] for number in keys]
        if numbers == range(len(numbers)) or numbers[0] == 0:
            # If the first key is different from zero, it can't be a list..
            # Process to become a list
            return [key[1] for key in keys]
    return dictionary
def processQueryString(qs):
    r = {}
    for item in qs.split("&"):
        item = item.split("=", 1)
        if not item[1:]:
            item[1] = None
        key, val = item
        if "[" in key:
            brackets = key.split("[")
            # It's a Array, and it's recursive
            children = r  # Children is just a pointer to r
            c = 0  # Initialize at zero
            l = len(brackets) - 1  # Length-1 to detect end
            for bracket in brackets:
                key_child = bracket.split("]")[0]
                if not key_child and c > 0:
                    key_child = str(len(children))
                children[key_child] = children.get(key_child, {})
                if c == l:
                    children[key_child] = urllib.unquote_plus(val)
                else:
                    children = children[key_child]  # Replaces the pointer
                c += 1
        else:
            # It's not a array \o/
            r[key] = urllib.unquote_plus(val)
    return convertToList(r)
class HTTPFileUpload(StringIO):
    '''Simulates a file object, extracted from a HTTP Upload'''
    def __init__(self, filename, content="", content_type=""):
        super(HTTPFileUpload, self).__init__(content)
        self.name = filename
        self.mode = "rb"
        self.contentType = content_type
    def getContentType(self):
        return self.contentType
class HTTPProtocol:
    '''Processes the HTTP Request progressively'''
    def __init__(self):
        self.__buffer__ = ""
        self.META = {"RAW_POST_DATA":""}
        self.GET = {}
        self.POST = {}
        self.COOKIES = {}
        self.FILES = {}
        self.HEADERS = {}
        self.__content__ = []
        self.write = self.__content__.extend
        self.status_code = 200
    def processFirstLine(self, content):
        self.__buffer__ += content
        if self.__buffer__.count("\r\n") > 1:
            two_lines = self.__buffer__.split("\r\n", 1)  # Get the first line
            self.__buffer__ = two_lines[1]
            self.META["METHOD"], self.META["PATH"], self.META["PROTOCOL"] = two_lines[0].split()
            self.META.update(zip(["PATH", "QUERYSTRING"], self.META["PATH"].split("?", 1) + [""]))
            self.addContent = self.processHeaders
            self.processFirstLine = None
            self.addContent("")  # Processes the next line in the buffer..if have it
    def processHeaders(self, content):
        '''Process the headers at possible'''
        self.__buffer__ += content
        if self.__buffer__.count("\r\n") > 1:
            header, self.__buffer__ = self.__buffer__.split("\r\n", 1)
            if header:
                header = header.split(": ", 1)
                self.META["HTTP_" + str(header[0]).upper()] = header[1]
            else:
                # Oh, a empty line..the next lines is the post content...
                self.addContent = self.processPostContent  # Replace the pointer to achieve performance
                self.processHeaders = None
                return None
            self.addContent("")  # Processes the next line in the buffer..if have it
    def processPostContent(self, content):
        '''Process and interpret the post content, always!'''
        ct = self.META.get("HTTP_CONTENT_TYPE", "") 
        self.META["RAW_POST_DATA"] += +content
        self.META["HTTP_CONTENT_LENGTH"] = int(self.META.get("HTTP_CONTENT_LENGTH", 0))
        if len(self.META["RAW_POST_DATA"]) < self.META["HTTP_CONTENT_LENGTH"]:  # Verify if the content length of the request has be reached
            return 
        # Process some variables of the request
        self.COOKIES = Cookie.SimpleCookie(self.META.get("HTTP_COOKIE", ""))      
        self.GET = processQueryString(self.META["QUERYSTRING"])
        if ct.startswith("application/x-www-form-urlencoded"):       
            self.POST = processQueryString(self.META["RAW_POST_DATA"])
        elif 'boundary=' in ct and ct.startswith("multipart/form-data"):
            boundary = ct.split('boundary=', 1)[1]
            if boundary: 
                if boundary.startswith('"') and boundary.endswith('"'):
                    boundary = boundary[1:-1]
                if self.META["RAW_POST_DATA"].endswith("\r\n"):
                    footer_length = len(boundary) + 6
                else:
                    footer_length = len(boundary) + 4
                parts = self.META["RAW_POST_DATA"][:-footer_length].split("--" + boundary + "\r\n")
                for part in parts:
                    if not part: 
                        continue
                    eoh = part.find("\r\n\r\n")
                    if eoh == -1:
                        continue
                    eoh += 2
                    headers = dict([line.split(": ") for line in part[:eoh].split("\r\n") if line.count(": ") == 1])  # Process headers 
                    name_header = headers.get("Content-Disposition", "")
                    if not name_header.startswith("form-data;") or not part.endswith("\r\n"):
                        continue
                    value = part[eoh + 2:-2]
                    name_values = {}
                    for name_part in name_header[10:].split(";"):
                        filename, name_value = name_part.strip().split("=", 1)
                        name_values[filename] = name_value.strip('"').decode("utf-8")                       
                    if not name_values.get("name"):
                        continue
                    fieldname = name_values["name"]
                    if name_values.get("filename"):
                        self.FILES[fieldname] = HTTPFileUpload(name_values["filename"], value, headers.get("Content-Type", "application/unknown"))
                    else:
                        self.POST[fieldname] = value        
            self.POST = convertToList(self.POST)
            self.FILES = convertToList(self.FILES)
        self.addContent = None  # There not content to process
        self.processPostContent = None
    def __call__(self, content="", mimetype='text/html', status=200):
        self.content = list(content)
        self.HEADERS['Content-type'] = mimetype
        self.status_code = status
        return self
    def set_cookie(self, key, value='', max_age=None, expires=None, path='/', domain=None, secure=None, httponly=False):
        self.COOKIES[key] = value
        if max_age:
            self.COOKIES[key]['max-age'] = max_age
        if expires:
            self.COOKIES[key]['expires'] = expires
        if path:
            self.COOKIES[key]['path'] = path
        if domain:
            self.COOKIES[key]['domain'] = domain
        if secure:
            self.COOKIES[key]['secure'] = secure
        if httponly:
            self.COOKIES[key]['httponly'] = httponly
    def __str__(self):
        if self.META["METHOD"] == "HEAD":
            self.content = []
        return "".join(["HTTP/1.1 " + str(self.status_code) + "\r\n"] + [["", self.COOKIES.__str__() + "\n"][self.COOKIES.__str__() != '']] + [k + ': ' + str(self.HEADERS[k]) + "\r\n"  for k in self.HEADERS] + ['\r\n'] + self.content)
