import re, timeit, profile, dis, os
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
	itens = (remapGET(separateKey(q)) for q in qs.split("&"))
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
	
detectRE = re.compile("&?([^&=]+)=?([^&]*)").findall
splitBrackets = re.compile("\[([^\]]*)\]").findall
def processWithRE(qs):
	#return dict(map(remapGET, re.findall("&?([^&=]+)=?([^&]*)", qs)))
	r = {}
	itens = (remapGET(q) for q in detectRE(qs))
	for key, val in itens:
		brackets = splitBrackets("[")
		if brackets:
			#It's a Array, and it's recursive
			children = r #Children is just a pointer to r
			c = 0 #Initialize at zero
			l = len(brackets)-1 #Length-1 to detect end
			is_end = lambda: c==l #Indicate if ends
			for key_child in brackets:
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
	#return dict(remapGET(q) for q in detectRE(qs))
#qs = createQueryString(10)
qs = "teste[0][0][]=rs&teste[0][0][]=oi&teste[0][]=aehaueahu&teste[0][]=aheauehau"
num_requests = 100000
print "Rodando %d requisicoes.."%num_requests
#print qs
def benchmark(func):
	print "-"*100
	print func.__name__
	print "-"*100
	dis.dis(func)
	profile.run("".join([func.__name__,"(qs)"]))
	result = timeit.timeit("".join([func.__name__,"(qs)"]),"".join(["from __main__ import ",func.__name__,", qs"]), number=num_requests)
	print num_requests,"=",result," segundos"
	return result
#print processWithRE(qs)
processWithURLParse.__name__ = "processWithURLParse"
funcs = [processWithMap, processWithRE, processWithURLParse]
if qs.count("[") > 1:
	funcs.pop() #URL Parse does not manage multiple brackets
results = map(benchmark, funcs)
print "-"*1000
print "Mais rapido:",funcs[results.index(min(results))].__name__,"(com ",min(results)," segundos)"
print "Mais lento:",funcs[results.index(max(results))].__name__,"(com ",max(results)," segundos)"