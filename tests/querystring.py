import re, timeit, profile, dis
from cgi import parse_qs as processWithURLParse
def createQueryString(n=10):
	return "&".join(map("=".join, [["".join(["key",str(c)]), "".join(["value",str(c)])] for c in xrange(n) ]))
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
	for key in d.iterkeys():
		if not key.isdigit() and key:
			is_list = False #It can't be a list..
			break
		elif key.isdigit() and key:
			keys.append(int(key))
	r = {}
	for key, val in d.iteritems():
		if isinstance(val, dict): #It's a dictionary!
			r[key] = convertToList(val)
		else:
			r[key] = val
	if is_list and keys:#It have keys?
		keys.sort()#Sorts the list
		if keys[0] != 0:
			#If the first key is different from zero, it can't be a list..
			return r
		#Process to become a list
		l = []
		for key in keys:
			l.insert(key, r[str(key)])
		return l 
	return r
def adaptGet(itens):
	r = {}
	for key, val in itens:
		brackets = key.split("[")
		if brackets:
			#It's a Array, and it's recursive
			children = r #Children is just a pointer to r
			c = 0 #Initialize at zero
			l = len(brackets)-1 #Length-1 to detect end
			is_end = lambda: c==l #Indicate if ends
			for bracket in brackets:
				key_child = bracket.split("]",1)[0]
				if not key_child and c>0:
					key_child = str(len(children))
				children[key_child] = children.get(key_child, {})
				if not is_end():
					children = children[key_child]#Replaces the pointer
				else:
					children[key_child] = val
				c += 1
		else:
			#It's not a array \o/
			r[key] = val
	return convertToList(r)
def processWithMap(qs):
	return adaptGet(remapGET(separateKey(q)) for q in qs.split("&"))
	
detectRE = re.compile("&?([^&=]+)=?([^&]*)").findall
def processWithRE(qs):
	#return dict(map(remapGET, re.findall("&?([^&=]+)=?([^&]*)", qs)))
	return adaptGet(remapGET(q) for q in detectRE(qs))
	#return dict(remapGET(q) for q in detectRE(qs))
#qs = createQueryString(10)
qs = "teste[0][0][]=rs&teste[0][0][]=oi"
print processWithRE(qs) == processWithMap(qs)
print processWithMap(qs)
num_requests = 10000
print "Rodando %d requisicoes.."%num_requests
#print qs
#print processWithMap(qs)
def benchmark(func):
	print "-"*100
	print func.__name__
	print "-"*100
	dis.dis(func)
	profile.run("".join([func.__name__,"(qs)"]))
	print timeit.timeit("".join([func.__name__,"(qs)"]),"".join(["from __main__ import ",func.__name__,", qs"]), number=num_requests)
#print processWithRE(qs)
processWithURLParse.__name__ = "processWithURLParse"
funcs = [processWithMap, processWithRE, processWithURLParse]
#map(benchmark, funcs)
