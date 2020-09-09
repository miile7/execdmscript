import execdmscript

dmscript1 = "number c = a + b;"
dmscript2 = "number d = c + a;"
dmscript3 = r"C:\testdmscript5.s"

setvars = {"a": 1, "b": 2}
readvars = {"c": int, "d": int, "e": int}

with execdmscript.exec_dmscript(dmscript1, dmscript2, dmscript3, setvars=setvars, 
								readvars=readvars) as script:
	print("c:", script["c"])
	print("d:", script["d"])
	print("e:", script["e"])