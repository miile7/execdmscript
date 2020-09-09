
import execdmscript

import urllib.request
import html.parser
import re

# get the text of example.com
content = str(urllib.request.urlopen("https://www.example.com/").read())

# get all headlines
matches = re.findall(r"<h([\d])>([^<]+)</h\1>", content)
if matches is not None:
	headlines = [x[1] for x in matches]
	text = "Headlines:\n- " + "\n- ".join(headlines)
else:
	headlines = []
	text = "*No headlines found*"

# Tell the dm-script the variables it should know
setvars = {"text": text}

# set your filepath, needs to be the complete path, not just the name!
path = r"C:\testdmscript.s"

with execdmscript.exec_dmscript(path, setvars=setvars):
	pass