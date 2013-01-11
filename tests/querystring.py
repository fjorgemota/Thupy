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
def processWithMap(qs):
	return dict(map(remapGET, map(separateKey, qs.split("&"))))
detectRE = re.compile("&?([^&=]+)=?([^&]*)").findall
def processWithRE(qs):
	#return dict(map(remapGET, re.findall("&?([^&=]+)=?([^&]*)", qs)))
	return dict(map(remapGET, detectRE(qs)))
	#return dict(remapGET(q) for q in detectRE(qs))
qs = createQueryString(1000)
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
map(benchmark, funcs)
