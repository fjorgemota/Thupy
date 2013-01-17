import re, timeit, profile, dis, os, functools, urllib
from cgi import parse_qs as processWithURLParse
def createQueryString(n=10, level=0):
	joinQueries = "=".join
	if not level:
		return "&".join(map(joinQueries, [["".join(["key",str(c)]), "".join(["value",str(c)])] for c in xrange(n) ]))
	else:
		query = []
		start = 0
		for levelc in xrange(level):
			query.extend(map(joinQueries, [["".join(["key",str(c),"[]"*levelc]), "".join(["value",str(c)])] for c in xrange(start, start+n) ]))
			start += n+1
		return "&".join(query)
def remapGET(q):
	#return [q[0],[None,q[1]][q[1:] != []]]
	return [q[0], None] if len(q) == 1 else [q[0], q[1]]
def validateKey(q):
	return q[0]
def separateKey(q):
	return q.split("=",1)
def convertToList(d):
	is_list = True #Indicates if can be a list
	keys = []
	for key, val in d.iteritems():
		if isinstance(val, dict): #It's a dictionary!
			d[key] = convertToList(val) #Recurse it!
		if is_list: #If flag is True..
			if not key.isdigit() and key: #Verify if it's not a number
				is_list = False #It can't be a list..
			elif key.isdigit() and key: #Verify if it's a number and...
				keys.append(int(key))#Add it to a list of keys \o/
	if is_list and keys:#It have keys and it's a list?
		keys.sort()#Sorts the list
		if keys[0] != 0:
			#If the first key is different from zero, it can't be a list..
			return d
		#Process to become a list
		l = []
		for key in keys:
			l.insert(key, d[str(key)])
		return l 
	return d
	
def processWithMap(qs):
	r = {}
	for item in qs.split("&"):
		key, val = remapGET(separateKey(item))
		brackets = key.split("[")
		if brackets:
			#It's a Array, and it's recursive
			children = r #Children is just a pointer to r
			c = 0 #Initialize at zero
			l = len(brackets)-1 #Length-1 to detect end
			for bracket in brackets:
				key_child = bracket.split("]",1)[0]
				if not key_child and c>0:
					key_child = str(len(children))
				children[key_child] = children.get(key_child, {})
				if c != l:
					children = children[key_child]#Replaces the pointer
				else:
					children[key_child] = urllib.unquote_plus(val)
				c += 1
		else:
			#It's not a array \o/
			r[key] = urllib.unquote_plus(val)
	return convertToList(r)
	
detectRE = re.compile("&?([^&=]+)=?([^&]*)").findall
splitBrackets = re.compile("\[([^\]]*)\]").findall
def processWithRE(qs):
	#return dict(map(remapGET, re.findall("&?([^&=]+)=?([^&]*)", qs)))
	r = {}
	for  item in detectRE(qs): #An iterator!
		key, val = remapGET(item) #Separate key and value
		brackets = splitBrackets(key)
		if brackets:
			#It's a Array, and it's recursive
			brackets.insert(0, key.split("[")[0])
			children = r #Children is just a pointer to r
			c = 0 #Initialize at zero
			l = len(brackets)-1 #Length-1 to detect end
			for key_child in brackets:
				if not key_child and c>0:
					key_child = str(len(children))
				children[key_child] = children.get(key_child, {})
				if c!=l:
					children = children[key_child]#Replaces the pointer			
				else: 
					children[key_child] = urllib.unquote_plus(val)
				c += 1
		else:
			#It's not a array \o/
			r[key] = urllib.unquote_plus(val)
	return convertToList(r)
	#return dict(remapGET(q) for q in detectRE(qs))
#qs = createQueryString(10)
qs = createQueryString(10,10)
print qs
qs2 = createQueryString(10)
num_requests = 10000
print "Rodando %d requisicoes.."%num_requests
def benchmark(func, qs_var_name):
	print "-"*100
	print func.__name__
	print "-"*100
	if os.name != "java":
		dis.dis(func)
	profile.run("".join([func.__name__,"(",qs_var_name,")"]))
	print "Resultado da funcao ",func.__name__,":",func(globals().get(qs_var_name))
	timer = timeit.Timer("".join([func.__name__,"(",qs_var_name,")"]),"".join(["from __main__ import ",func.__name__,", ",qs_var_name]))
	result = timer.timeit(num_requests)
	print num_requests," requisicoes =",result," segundos"
	return result
#print processWithRE(qs)
processWithURLParse.__name__ = "processWithURLParse"
def testAll(qs_var_name):
	funcs = [processWithMap, processWithRE, processWithURLParse]
	if globals().get(qs_var_name).count("[") > 1:
		funcs.pop() #URL Parse does not manage multiple brackets
	results = map(functools.partial(benchmark, qs_var_name=qs_var_name), funcs)
	#results = []
	print "-"*100
	print "Ranking:"
	for position, duration in enumerate(sorted(results)):
		print position+1," lugar - ",funcs[results.index(duration)].__name__," - Com ",duration," segundos"
	return results
if __name__ == "__main__":
	print "Com sub-chaves:"
	testAll("qs")
	print "-"*120
	print "Sem sub-chaves:"
	testAll("qs2")