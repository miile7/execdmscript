import execdmscript

# `a` and `b` are given in python
a = 10
b = 20

# This is the dm-script to execute
dmscript = "number c = a + b;"

# This are the variables the upper dm-script will know
setvars = {"a": a, "b": b}

# This are the variables this python script will know after the execution
readvars = {"c": int}

with execdmscript.exec_dmscript(dmscript, setvars=setvars, readvars=readvars) as script:
	# now we can access `c` because it is set in the `readvars`
	print(script["c"])