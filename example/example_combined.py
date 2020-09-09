"""This is an example file of how to use the `execdmscript` module."""

# = = = = = = = = = = = = = =  IGNORE START = = = = = = = = = = = = = = = = = =
# Ignore the following code until the second line
#
# This code is for getting the __file__. GMS does not set the __file__ variable
# on running scripts. That causes the example file not to run properly except
# the execdmscript module is in one of the GMS plugin directories.
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
try:
	import DigitalMicrograph as DM
	in_digital_micrograph = True
except ImportError:
	in_digital_micrograph = False

file_is_missing = False
try:
	if __file__ == "" or __file__ == None:
		file_is_missing = True
except NameError:
	file_is_missing = True

if in_digital_micrograph and file_is_missing:
	# the name of the tag is used, this is deleted so it shouldn't matter anyway
	file_tag_name = "__python__file__"
	# the dm-script to execute, double curly brackets are used because of the 
	# python format function
	script = ("\n".join((
		"DocumentWindow win = GetDocumentWindow(0);",
		"if(win.WindowIsvalid()){{",
			"if(win.WindowIsLinkedToFile()){{",
				"TagGroup tg = GetPersistentTagGroup();",
				"if(!tg.TagGroupDoesTagExist(\"{tag_name}\")){{",
					"number index = tg.TagGroupCreateNewLabeledTag(\"{tag_name}\");",
					"tg.TagGroupSetIndexedTagAsString(index, win.WindowGetCurrentFile());",
				"}}",
				"else{{",
					"tg.TagGroupSetTagAsString(\"{tag_name}\", win.WindowGetCurrentFile());",
				"}}",
			"}}",
		"}}"
	))).format(tag_name=file_tag_name)

	# execute the dm script
	DM.ExecuteScriptString(script)

	# read from the global tags to get the value to the python script
	global_tags = DM.GetPersistentTagGroup()
	if global_tags.IsValid():
		s, __file__ = global_tags.GetTagAsString(file_tag_name);
		if s:
			# delete the created tag again
			DM.ExecuteScriptString(
				"GetPersistentTagGroup()." + 
				"TagGroupDeleteTagWithLabel(\"{}\");".format(file_tag_name)
			)
		else:
			del __file__

	try:
		__file__
	except NameError:
		# set a default if the __file__ could not be received
		__file__ = ""

# = = = = = = = = = = = = = = = IGNORE END = = = = = = = = = = = = = = = = = =

# The start of the example file

import os
import sys
import pprint
import traceback

if __file__ != "":
	# add the parent directory to the system path so the execdmscript file
	# can be imported
	base_path = str(os.path.dirname(os.path.dirname(__file__)))
	
	if base_path not in sys.path:
		sys.path.insert(0, base_path)

import execdmscript

try:
	script1 = """
	number a = 40;
	number c = a + b;
	string d = \"This is a test string\";
	"""

	script2 = os.path.join(os.path.dirname(__file__), "example_combined.s")

	script3 = """
	TagGroup tg3 = NewTagGroup();

	index = tg3.TagGroupCreateNewLabeledTag("a");
	tg3.TagGroupSetIndexedTagAsFloat(index, 10.0001);
	index = tg3.TagGroupCreateNewLabeledTag("b");
	tg3.TagGroupSetIndexedTagAsFloat(index, 11.0002);

	TagGroup tl2 = newTagList();
	"""

	parent = os.path.expanduser("~")
	home_dirs = []
	for e in os.listdir(parent):
		if os.path.isdir(os.path.join(parent, e)):
			script3 += "tl2.TagGroupInsertTagAsString(infinity(), \"{}\");\n".format(
				str(e).replace("\\", "\\\\").replace("\"", "\\\"")
			)
			home_dirs.append(e)

	script3 += """
	index = tg3.TagGroupCreateNewLabeledTag("files");
	tg3.TagGroupSetIndexedTagAsTagGroup(index, tl2);

	TagGroup tl3 = NewTagList();
	tl3.TagGroupInsertTagAsString(infinity(), "a");
	tl3.TagGroupInsertTagAsString(infinity(), "b");

	TagGroup tl4 = NewTagList();
	tl4.TagGroupInsertTagAsString(infinity(), "c");
	tl4.TagGroupInsertTagAsNumber(infinity(), 5);

	TagGroup tl5 = NewTagList();
	tl5.TagGroupInsertTagAsString(infinity(), "d");
	"""

	readvars = {
		"a": int,
		"b": "number",
		"c": "dOuBle",
		"d": str,
		"tg1": "TagGroup",
		"tg3": {
			"a": "float",
			"b": float,
			"files": [str] * len(home_dirs)
		},
		"tl3": "TagList",
		"tl4": [str, int],
		"tl5": list
	}
	setvars = {
		"b": -193.3288,
		"tg4": {
			"test-key 1": 1,
			"test-key 2": {
				"test-key 3": False,
				"test-key 4": None
			}
		},
		"tl6": [
			"A", "B", ["U", "V"], (-101, -120)
		]
	}

	with execdmscript.exec_dmscript(script1, script2, script3, 
									readvars=readvars, setvars=setvars, 
									separate_thread=False,
									debug=False, debug_file=None) as script:
		for key in script.synchronized_vars.keys():
			print("Variable '", key, "'")
			pprint.pprint(script[key])

	# wrapper = execdmscript.DMScriptWrapper(script1, script2, script3, 
	# 										 readvars=readvars, setvars=setvars)
	#
	# exec_script = wrapper.getExecDMScriptCode()
	#
	# print("The following script is being executed:")
	# print(exec_script)
except Exception as e:
	# dm-script error messages are very bad, use this for getting the error text and the 
	# correct traceback
	print("Exception: ", e)
	traceback.print_exc()