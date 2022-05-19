import threading
import math
import random

def timeWaste(num):
	for _ in range(num ** 2):
		x = num % num / math.cos(num) + 20210421041204124012401240
	y = [math.sin(x) + math.cos(x ** 2) for x in range(1000)]
	return x, y

def do(lst):
	for i in lst:
		i = timeWaste(i)

lst1 = [random.randint(1, 100) for _ in range(200)]

import time
x = threading.Thread(target=do, args=[lst1[:49],])
y = threading.Thread(target=do, args=[lst1[50:100],])
start = time.perf_counter_ns()
x.start()
y.start()
x.join()
y.join()
print('Function took:', str(time.perf_counter_ns() - start))

# no threading   : 652025200
# with threading : 313432300