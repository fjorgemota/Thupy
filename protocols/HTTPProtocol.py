'''
Created on 08/01/2013

@author: fernando
'''
class RequestHandler:
    def __init__(self, content="", ip="",sock=None):
        headers = content.split("\r\n\r\n",1)
        lines = headers[0].split("\r\n")
        http = lines[0].split(" ",2)
        qstr = http[1].split("?",1)
        self.META = {
                     "REMOTE_ADDR":ip,
                     "RAW_POST_DATA":headers[1],
                     "QUERY_STRING":qstr[-1],
                     "PATH":qstr[0],
                     "METHOD":http[0],
                     "PROTOCOL":http[2].strip(),
                     "HEADERS_LINES":lines[1:]
        }
        self.sock = sock
        v = filter(lambda x: "host" in x.lower(),lines)
        if v:
            v = v[0].split(": ",1)[1]
        else:
            v = None
        self.METAH_HOST = v
    def __call__(self, content="", mimetype='text/html', status=200):
        self.content = list(content)
        self.HEADERS['Content-type'] = mimetype
        self.status_code = status
        return self
    def __getattr__(self,name):
        if name == "COOKIES":
            self.COOKIES = Cookie.SimpleCookie(self.METAH_COOKIE or "")
        elif name == "write":
            self.write = self.content.extend   
        elif name == "status_code":
            self.status_code = 200  
        elif name == "content":
            self.content = []
        elif name == "HEADERS":
            self.HEADERS = {"Content-type":"text/html; charset=utf-8", "Server":"Choice"}
        elif name[:6] == "METAH_":
            n = name[6:].lower().replace("_","-")
            v = filter(lambda x: n in x.lower(),self.META["HEADERS_LINES"])
            if v:
                v = v[0].split(": ",1)[1]
            else:
                v = None
            setattr(self,name,v)
        elif name == "METAH":
            self.METAH = dict(map(lambda i:[i[0].upper().replace('-', '_'), i[1]],map(lambda x:x.split(": ",1),self.META["HEADERS_LINES"])))
        elif name[:5] == "META_":
            setattr(self,name,self.META.get(name[5:]))
        elif name == "GET":
            self.GET = {}        
            arguments = urlparse.parse_qs(self.META.get("QUERY_STRING",""))
            for _name, values in arguments.iteritems():
                self.GET[_name] = [v for v in values if v]
                if not self.GET[_name][1:]:
                    self.GET[_name] = self.GET[_name][0]
        elif name[:4] == "GET_":
            v = filter(str.strip,map(lambda x:urllib.unquote_plus(x.split("&")[0]),self.META_QUERY_STRING.split("".join([name[4:],"="]))[1:]))
            if not v:
                v = None
            elif not v[1:]:
                v = v.pop(0)
            setattr(self,name,v)
        elif name == "POST":  
            self.POST = {}  
            ct = self.METAH_CONTENT_TYPE or "" 
            if ct.startswith("application/x-www-form-urlencoded"):       
                arguments = urlparse.parse_qs(self.META["RAW_POST_DATA"])
                for _name, values in arguments.iteritems():
                    self.POST[_name] = [v for v in values if v]
                    if not self.POST[_name][1:]:
                        self.POST[_name] = self.POST[_name][0]
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
                        headers = dict([[n, v] for n, v in regex_headers.findall(part[:eoh])]) 
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
                        filename = name_values["name"]
                        if name_values.get("filename"):
                            ctype = headers.get("Content-Type", "application/unknown")
                            self.POST[filename] = {"filename":name_values["filename"], "body":value, "content_type":ctype}
                        else:
                            self.POST[filename] = value
        elif name[:5] == "POST_":
            v = None
            ct = self.META.get("CONTENT_TYPE","")
            content = self.META["RAW_POST_DATA"]
            if ct.startswith("application/x-www-form-urlencoded"):  
                v = filter(str.strip,map(lambda x:x.split("&")[0],content.split("".join([name[5:],"="]))))
                if not v[1:]:
                    v = v.pop(0)
                elif not v:
                    v = None
            elif 'boundary=' in ct and ct.startswith("multipart/form-data"):
                boundary = ct.split('boundary=', 1)[1]
                if boundary: 
                    if boundary.startswith('"') and boundary.endswith('"'):
                        boundary = boundary[1:-1]
                    if content.endswith("\r\n"):
                        footer_length = len(boundary) + 6
                    else:
                        footer_length = len(boundary) + 4
                    parts = content[:-footer_length].split("--" + boundary + "\r\n")
                    for part in parts:
                        if not part and nm in part: 
                            continue
                        eoh = part.find("\r\n\r\n")
                        if eoh == -1:
                            continue
                        headers = dict([[n, v] for n, v in re.findall("([^:]*):\s([^\r]*)\r\n?", part[:eoh])]) 
                        name_header = headers.get("Content-Disposition", "")
                        if not name_header.startswith("form-data;") or not part.endswith("\r\n"):
                            continue
                        value = part[eoh + 4:-2]
                        name_values = {}
                        for name_part in name_header[10:].split(";"):
                            name, name_value = name_part.strip().split("=", 1)
                            name_values[name] = name_value.strip('"').decode("utf-8")
                        if not name_values.get("name"):
                            continue
                        name = name_values["name"]
                        if name_values.get("filename"):
                            ctype = headers.get("Content-Type", "application/unknown")
                            v = {"filename":name_values["filename"], "body":value, "content_type":ctype}
                        else:
                            v = value
            setattr(self,name,v)            
        elif name == "lang":
            try:
                self.lang = self.COOKIES["user_lang"].value.split("|")
                if self.lang[1] != self.META.get("ACCEPT_LANGUAGE"):
                    raise Exception()
                self.lang = self.lang[0]
                if not languages.get(self.lang):
                    raise Exception()
            except:
                if (getattr(self, "USER", {"language":False}) or {}).get("language"):
                    lang = self.USER["language"]
                else:
                    lang = "pt-br"
                    try: 
                        lang = cache.get("al_" + str(self.META.get("ACCEPT_LANGUAGE", "")))
                        if not lang:
                            lang = lang or "pt-br"
                            LANGS = [acceptlanguagere.match(l).groups() for l in self.META.get("ACCEPT_LANGUAGE", "").split(",")]
                            p = 1
                            LANGS.reverse()
                            c = 0
                            for l in LANGS:
                                LANGS[c] = list(LANGS[c])
                                if l[2]:
                                    p = l[2]
                                else:
                                    LANGS[c][2] = p 
                                if l[1]:
                                    LANGS[c][0] = "-".join(l[0:2])
                                del LANGS[c][1] 
                                c += 1
                            LANGS.reverse()
                            p = 0
                            for k, v in LANGS:
                                
                                if p < float(v) and languages.get(k):
                                    lang = k.lower()
                                    p = v
                            cache.set("al_" + str(self.META.get("ACCEPT_LANGUAGE", "")), lang, 3600)
                    except:
                        lang = "pt-br"
                        e = True         
                self.set_cookie("user_lang", lang + str("|") + self.META.get("ACCEPT_LANGUAGE", ""), max_age=86400,expires=datetime.datetime.fromtimestamp(time.time()+86400,pytz.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")) 
            self.lang = lang
        elif name == "layout":
            self.layout = None
        elif name in ("_","template"):
            self.template = templates[self.SITE_domain][self.lang]
            self._ = languages[self.SITE["domain"]][self.lang].gettext
        elif name=="SITE":
            host = self.METAH.get("HOST") or criewebsites.find_one(fields=["domain"])["domain"]     
            host = host.replace("www.", "")
            ch = "".join(["domain_",md5(str(host)).hexdigest()])
            self.SITE = cache.get(ch)
            if not self.SITE:
                self.SITE = criewebsites.find_one({"domain":host}) or {}
                cache.set(ch, self.SITE, 3600)
        elif name[:5]=="SITE_":
            host = self.METAH.get("HOST") or criewebsites.find_one(fields=["domain"])["domain"]     
            host = host.replace("www.", "")
            v = cache.get("".join(["domain_",md5(str(host)).hexdigest()]))
            if not v:
                ch = "".join(["domain_",md5(str(host)+str(name[5:])).hexdigest()])
                v = cache.get(ch)
                if not v:
                    v = criewebsites.find_one({"domain":host}, fields=[name[5:]]) or {}
                    cache.set(ch, v, 3600)
            if not v:
                v = {}
                v[name[5:]] = None
            setattr(self,name,v.get(name[5:]))
        elif name=="SITEGET":
            host = self.GET.get("domain") or self.META.get("HOST") or criewebsites.find_one(fields=["domain"])["domain"]                   
            host = host.replace("www.", "")
            ch = "".join(["domain_",md5(str(host)).hexdigest()])
            self.SITEGET = cache.get(ch)
            if not self.SITEGET:
                self.SITEGET = criewebsites.find_one({"domain":host}, fields=[field for field in fields if field in self.SITE.keys()] or None) or {}
                cache.set(ch, self.SITEGET, 3600)
        elif name[:8]=="SITEGET_":
            host = self.GET.get("domain") or self.META.get("HOST") or criewebsites.find_one(fields=["domain"])["domain"]     
            host = host.replace("www.", "")
            v = cache.get("".join(["domain_",md5(str(host)).hexdigest()]))
            if not v:
                ch = "".join(["domain_",md5(str(host)+str(name[8:])).hexdigest()])
                v = cache.get(ch)
                if not v:
                    v = criewebsites.find_one({"domain":host}, fields=[name[8:]]) or {}
                    cache.set(ch, v, 3600)
            setattr(self,name,v[name[8:]])
        elif name == "USER":
            self.USER = None
        else:
            raise AttributeError()
        return getattr(self, name)
    def render(self,layout,data={},g = None):
        data = data or {}
        data.update({"_":self._,"req":self})
        if self.layout is None:
            if not hasattr(self,"SESSION"):
                self = session(self)
            if self.SESSION.get("userid") and self.USER:
                self.layout = "layout.authenticated.html"
            else:
                self.layout = "layout.unauthenticated.html"
        if not self.USER and self.layout is None:
            self.layout = "layout.unauthenticated.html"
        data.update({"user":self.USER})
        self(self.template.render(layout,data,g,self.layout))
        self.HEADERS["Content-Length"] = len(self.content)
        return self
    def __toXML(self, x, data, resource):
        if isinstance(data, (list, tuple)):
            for item in data[1:]:
                x.startElement(resource, {})
                self.__toXML(x, item, resource[0])
                x.endElement(resource)
        elif isinstance(data, dict):
            for key, value in [(k, v) for k, v in data.iteritems() if k != 'key']:
                x.startElement(key, {})
                self.__toXML(x, value, data["key"])
                x.endElement(key)
        else:
            x.characters(smart_unicode(data))    
    def format(self, data, format='xml', formats=['xml', 'json', 'yaml', 'txt'], parent='response'):
        format = format.lower()
        if 'xml' in formats and 'xml' == format:
            stream = StringIO()
            
            x = xml.sax.saxutils.XMLGenerator(stream, "utf-8")
            x.startDocument()
            x.startElement(parent, {})
            
            self.__toXML(x, data)
            
            x.endElement(parent)
            x.endDocument()
            
            self(stream.getvalue(),'application/xml')
        elif 'json' in formats and 'json' == format:
            if simplejson:
                self("",'text/javascript; charset=UTF-8')
                if self.GET.get("callback", False):
                    self.write(self.GET.get("callback", ""))
                    self.write("(")
                self.write(simplejson.dumps(data, ensure_ascii=False).encode("UTF-8"))
                if self.GET.get("callback", False):
                    self.write(");")
            else:
                raise "Module SimpleJSON is not available"
        elif 'yaml' in formats and 'yaml' == format:
            if yaml:
                self(yaml.safe_dump(dict(data), default_flow_style=False),'application/x-yaml')
            else:
                raise "Module YAML is not Available"
        elif 'txt' in formats and 'txt' == format:
            self(str(data),'text/plain')
        else:
            return False
        return True
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