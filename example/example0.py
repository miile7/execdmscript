import execdmscript

# set the text in python
world_text = "Hello World!"

# create an executable dm-script code
dmscript = """
OKDialog(text);
result(text);
"""

# save which variables should be passed from python to dm-script and how they should be 
# called
setvars = {
	"text": world_text
}

# execute the script
with execdmscript.exec_dmscript(dmscript, setvars=setvars):
	pass