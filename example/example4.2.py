import execdmscript

# Tell the dm-script the variables it should know
setvars = {"variable1": "Executed from python", "variable2": 99999}

# set your filepath, needs to be the complete path, not just the name!
path = r"C:\testdmscript4.2.s"

with execdmscript.exec_dmscript(path, setvars=setvars):
	pass