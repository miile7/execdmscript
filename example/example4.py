import execdmscript

# Tell the dm-script the variables it should know
setvars = {"variable1": 1, "variable2": "B", "variable3": False}

# Get the list of headlines
readvars = {"variable4": str, "variable5": int}

# set your filepath, needs to be the complete path, not just the name!
path = r"C:\testdmscript3.s"

with execdmscript.exec_dmscript(path, setvars=setvars, readvars=readvars, debug=True,
								debug_file=r"C:\debugfile.s") as script:
	pass