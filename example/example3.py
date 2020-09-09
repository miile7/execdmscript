
import execdmscript

headlines = [
	"Section 1",
	"Section 2", 
	"Section 3"
]

# Tell the dm-script the variables it should know
setvars = {"headlines": headlines}

# Get the list of headlines
readvars = {"headline_texts": list}

# set your filepath, needs to be the complete path, not just the name!
path = r"C:\testdmscript2.s"

text = ""
with execdmscript.exec_dmscript(path, setvars=setvars, readvars=readvars) as script:
	for section in script["headline_texts"]:
		text += "**{}**\n{}\n\n".format(section["headline"], section["text"])

if text != "":
	print(text)
else:
	print("Could not find any sections.")