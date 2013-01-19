import re, timeit, profile, dis, os, functools, urllib, operator
from cgi import parse_qs as processWithURLParse
def createQueryString(n=10, level=0):
	joinQueries = "=".join
	if not level:
		return "&".join(map(joinQueries, [["".join(["key", str(c)]), "".join(["value", str(c)])] for c in xrange(n) ]))
	else:
		query = []
		start = 0
		for levelc in xrange(level):
			query.extend(map(joinQueries, [["".join(["key", str(c), "[]"*levelc]), "".join(["value", str(c)])] for c in xrange(start, start + n) ]))
			start += n + 1
		return "&".join(query)
def remapGET(q):
	# return [q[0],[None,q[1]][q[1:] != []]]
	return [q[0], None] if len(q) == 1 else [q[0], q[1]]
def validateKey(q):
	return q[0]
def separateKey(q):
	return q.split("=", 1)
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
		if numbers != range(len(numbers)) or numbers[0] != 0:
			# If the first key is different from zero, it can't be a list..
			return dictionary
		else:
			# Process to become a list
			return [key[1] for key in keys]
	return dictionary
def processWithMap(qs):
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
	
detectRE = re.compile("&?([^&=]+)=?([^&]*)").findall
splitBrackets = re.compile("\[([^\]]*)\]").findall
def processWithRE(qs):
	# return dict(map(remapGET, re.findall("&?([^&=]+)=?([^&]*)", qs)))
	r = {}
	for item in detectRE(qs):  # An iterator!
		if not item[1:]:
			item = list(item)
			item[1] = None
		key, val = item
		if "[" in key:
			brackets = splitBrackets(key)
			# It's a Array, and it's recursive
			brackets.insert(0, key.split("[")[0])
			children = r  # Children is just a pointer to r
			c = 0  # Initialize at zero
			l = len(brackets) - 1  # Length-1 to detect end
			for key_child in brackets:
				if not key_child and c > 0:
					key_child = str(len(children))
				children[key_child] = children.get(key_child, {})
				if c != l:
					children = children[key_child]  # Replaces the pointer			
				else: 
					children[key_child] = urllib.unquote_plus(val)  # set the value
				c += 1
		else:
			# It's not a array \o/
			r[key] = urllib.unquote_plus(val)
	return convertToList(r)
	# return dict(remapGET(q) for q in detectRE(qs))
# qs = createQueryString(10)
# print processWithMap(createQueryString(10, 10))
# os._exit(0)
qs = createQueryString(10, 10)
repeat = 2
qs2 = createQueryString(10)
num_requests = 10000
print "Rodando %d requisicoes.." % num_requests
def benchmark(func, qs_var_name):
	print "-"*100
	print func.__name__
	print "-"*100
	if os.name != "java":
		dis.dis(func)
	profile.run("".join([func.__name__, "(", qs_var_name, ")"]))
	print "Resultado da funcao ", func.__name__, ":", func(globals().get(qs_var_name))
	timer = timeit.Timer("".join([func.__name__, "(", qs_var_name, ")"]), "".join(["from __main__ import ", func.__name__, ", ", qs_var_name]))
	result = timer.repeat(repeat, num_requests)
	print num_requests, " requisicoes:"
	print "Mais rapido: ", min(result), " segundos"
	print "Mais lento: ", max(result), " segundos"
	print "Diferenca entre mais lento e mais rapido: ", max(result) - min(result), " segundos"
	print "Media: ", sum(result) / repeat, " segundos"
	print "Media por execucao: ", (sum(result) / repeat) / num_requests, " segundos"
	print "Total para ", repeat, " requisicoes: ", sum(result), " segundos"
	return sum(result) / repeat
# print processWithRE(qs)
processWithURLParse.__name__ = "processWithURLParse"
def testAll(qs_var_name):
	funcs = [processWithMap, processWithRE, processWithURLParse]
	if globals().get(qs_var_name).count("[") > 1:
		funcs.pop()  # URL Parse does not manage multiple brackets
	results = map(functools.partial(benchmark, qs_var_name=qs_var_name), funcs)
	# results = []
	print "-"*100
	print "Ranking:"
	for position, duration in enumerate(sorted(results)):
		print position + 1, " lugar - ", funcs[results.index(duration)].__name__, " - Com ", duration, " segundos"
	return results
if __name__ == "__main__":
	print "Com sub-chaves:"
	testAll("qs")
	print "-"*120
	print "Sem sub-chaves:"
	testAll("qs2")
