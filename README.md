# execdmscript

A Python module for executing DM-Script from Python in 
[Gatan Microscopy Suite (GMS) (Digital Micrograph) Version 3.4 or later](https://www.gatan.com/products/tem-analysis/gatan-microscopy-suite-software).

**Table of Contents**

1. [Foreword](#foreword)
2. [Usage](#usage)
	1. [Step by step examples](#step-by-step-examples)
		1. [Hello world](#example-0-hello-world)
		2. [Getting started](#example-1-getting-started)
		3. [Outhouse code](#example-2-outhouse-code)
		4. [TagGroups and TagLists](#example-3-taggroups-and-taglists)
		5. [Debug your code](#example-4-debug-your-code)
		6. [Multiple scripts](#example-5-multiple-scripts)
		7. [More examples](#more-examples)
	2. [One glance example](#one-glance-example)
	3. [Helper functions](#helper-functions)
		1. [Type mapping](#type-mapping)
		2. [Escaping code](#escaping-code)
		3. [Converting TagGroups](#converting-taggroups)
		4. [Remove global tags](#remove-global-tags)
3. [Installation](#installation)
4. [License and Publications](#license-and-publications)

## Foreword

This module is created because I needed to use DM-Scripts Dialogs in my project. But this
project was written in Python. Because there is no Python implementation for dialogs I 
decided to execute DM-Script that creates the dialogs. But then getting data from one to
the other programming language was more difficult than I thought. This module tries to 
solve those problems and hide verything away.

## Usage

> **Important**:
> 
> This module is for running DM-Script scripts **within and only within** the Python 
> interpreter of a running GMS (DigitalMicrograph). So you must only use this when you 
> are in a Python script window in GMS (DigitalMicrograph). This **does not work in the 
> command line!**

After the [installation](#installation) you can execute the following examples. Check out
the [one glance example](#one-glance-example) if you used this module already and just 
forgot how it worked. If you have never dealt with Python in GMS or you are new to 
`execdmscript`, check out the [step by step examples](#step-by-step-examples) below.

### Step by step examples

The following examples are taken from the *examples* directory which can also be found on 
the [github page](https://github.com/miile7/execdmscript/tree/master/example).

#### Example 0: Hello World

Because of tradition, let's do the hello world first. Obviously this is a lot more 
complicated than actually needed, but it teaches the basics.

```python
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
```

#### Example 1: Getting started

After the [installation](#installation) open GMS (DigitalMicrograph). Create a new script
window (<kbd>Ctrl</kbd> + <kbd>K</kbd>) and make sure it is set to *Python*  as the 
scripting language. For this example it does not matter if the script is executed in the 
background or not. Now type in (or copy) the following code:

```python
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
```

This script calculates `a` + `b`. But `a` and `b` are Python variables while `c` is a 
variable created in dm-script.

The `setvars` is a `dict` that takes the variable name as the key and the variable value
as its value. These values with their names will be accessable in the executed dm-script.
Values of the types `int`, `float`, `bool`, `str`, `list` and `dict` are
supported. They will be converted to their dm-script equivalent. This means `int`, `float`
and `bool` will be of the type `number`. `str` will be `string`. And `list` and `dict` 
will both be `TagGroup`s but the former will be a `TagList` and the latter will be a 
"true" `TagGroup`.

The `readvars` is a `dict` that takes the dm-script variable name as the key and the type
to expect as the value. This means that all the variables that have a key in the 
`readvars` and are defined in the executed dm-script will later be accessable in Python.

#### Example 2: Outhouse code

> **Important**:
> 
> When you are trying the example code, make sure you always know the complete path of 
> the dm-script *.s file in your Python script. It is not enough to have the file name 
> only!

Now let's go a little bit more complicated. There is no need to execute a sum operation in
dm-script.

This time we will create two files. The first one will be a dm-script file, the second one
will be a Python file again.

Open GMS and create a new dm-script window. Enter the following code and save it to 
somewhere where it is easy to find, say `C:\testdmscript2.s`.

```c
TagGroup dlg, dlg_items, field;

dlg = DLGCreateDialog("Headlines of website", dlg_items);

// Note that the `text` is neither initialized nor declared, that is important as it will
// be done by the python script!
field = DLGCreateLabel(text);
field.DLGWidth(100);
field.DLGHeight(4);

dlg.DLGAddElement(field);

alloc(UIFrame).init(dlg).pose();
```

As said, save the file somewhere, say `C:\testdmscript2.s`.

Now open a new Python script window in GMS. Create the following code:

```python
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
path = r"C:\testdmscript2.s"

with execdmscript.exec_dmscript(path, setvars=setvars):
	pass
```

This will create a dm-script dialog that shows all headlines of the website stated in the
code, in this case `example.com`.

This time the dm-script is in a separate file which is strongly recommended. This way the 
dm-script file can be debugged a lot easier. Also the code is better to read and 
structured in a better way.

Also as one can see, this are just a few Python lines but will be very hard to get with 
pure dm-script. On the other hand there no GMS-dialogs in Python.

#### Example 3: TagGroups and TagLists

> **Important**:
> 
> When you are trying the example code, make sure you always know the complete path of 
> the dm-script *.s file in your Python script. It is not enough to have the file name 
> only!

While Python has `list`s and `dict`s (and a lot more of course) for dealing with multiple
values, dm-script does that with `TagList`s and `TagGroup`s. Both are more less equivalent
even though the handling is very different. Therefore `execdmscript` converts both types
automatically.

Open GMS again and create a new Python script window. Create the following code:

```c
TagGroup dlg, dlg_items, wrapper, inputs;

dlg = DLGCreateDialog("Add text to the headlines", dlg_items);
wrapper = DLGCreateGroup();
wrapper.DLGTableLayout(2, headlines.TagGroupCountTags(), 0);

inputs = NewTagList();
for(number i = 0; i < headlines.TagGroupCountTags(); i++){
	string text;
	if(headlines.TagGroupGetIndexedTagAsString(i, text)){
		TagGroup label = DLGCreateLabel("Text for " + text, 25);
		wrapper.DLGAddElement(label);
		
		TagGroup input = DLGCreateStringField("");
		input.DLGIdentifier("input-" + i);
		wrapper.DLGAddElement(input);
		inputs.TagGroupInsertTagAsTagGroup(infinity(), input);
	}
}

dlg.DLGAddElement(wrapper);

object dialog = alloc(UIFrame).init(dlg);

// make sure the variable always exists, it may be empty but 
// it has to be declared!
TagGroup headline_texts = NewTagList();

if(dialog.pose()){
	for(number i = 0; i < headlines.TagGroupCountTags(); i++){
		string text;
		if(headlines.TagGroupGetIndexedTagAsString(i, text)){
			TagGroup input;
			inputs.TagGroupGetIndexedTagAsTagGroup(i, input);
			
			TagGroup vals = NewTagGroup();
			vals.TagGroupCreateNewLabeledTag("headline");
			vals.TagGroupSetTagAsString("headline", text);
			
			vals.TagGroupCreateNewLabeledTag("text");
			vals.TagGroupSetTagAsString("text", input.DLGGetStringValue());
			
			headline_texts.TagGroupInsertTagAsTagGroup(infinity(), vals);
		}
	}
}
```

This creates a dialog that shows all headlines in the `headlines` `TagList` and allows to
add texts to them. Save this file with any name, say `C:\testdmscript3.s`.

Now open a new Python script window in GMS. Create the following code:

```python
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
path = r"C:\testdmscript3.s"

text = ""
with execdmscript.exec_dmscript(path, setvars=setvars, readvars=readvars) as script:
	for section in script["headline_texts"]:
		text += "**{}**\n{}\n\n".format(section["headline"], section["text"])

if text != "":
	print(text)
else:
	print("Could not find any sections.")
```

The `script["headline_texts"]` is a list containing `dict`s because `TagList`s are 
converted to `list`s automatically and `TagGroup`s to `dict`s.

#### Example 4: Debug your code

The downside of using combined scripts is that one cannot really see what the dm-script 
interpreter is actually doing. For this problem there is a debug mode. Simply use
`execdmscript.exec_dmscript(code, debug=True, debug_file=file_path)` to get the dm-script
file that normally would be executed.

Let's assume that the file `C:\testdmscript4.s` exists and contains any code (if you want 
you can create this file and see what happens). To debug the complete file check out the 
following example Python code:

```python
import execdmscript

# Tell the dm-script the variables it should know
setvars = {"variable1": 1, "variable2": "B", "variable3": False}

# Get the list of headlines
readvars = {"variable4": str, "variable5": int}

# set your filepath, needs to be the complete path, not just the name!
path = r"C:\testdmscript4.s"

with execdmscript.exec_dmscript(path, setvars=setvars, readvars=readvars, debug=True,
								debug_file=r"C:\debugfile.s") as script:
	pass
```

This code will not execute dm-script code! But it will instead create the file at 
`C:\debugfile.s` that includes all the synchronization mechanisms that the `setvars` and
`readvars` need to work. This way you may find and fix bugs. Note that the `debug_file` 
is ignored when `debug` is not `True`.

To be able to run the code with and without python, one can use the start and end markers
to tell `execdmscript` to ignore the current part. In fact, this part will simply be 
commented out before execution. 

Create the following code and save it as `C:\testdmscript4.2.s`.

```c
// @execdmscript.ignore.start
// all the code here will never be executed except this
// dm-script code is executed manually
string variable1 = "Test";
number variable2 = 1;
result("This will not be printed when executed via python.\n")
// @execdmscript.ignore.end

result(variable1 + "\n");
result(variable2 + "\n");

// @execdmscript.ignore.start
result("Ignored again")
// @execdmscript.ignore.end
```

This is a valid dm-script file. It can be executed as it is. But as the comment already 
sais, the python execution via `execdmscript` will not see the lines between 
`@execdmscript.ignore.start` and `@execdmscript.ignore.end`.

One can see this by executing the above file in GMS. Then create the following python file
and execute it in GMS.

```python
import execdmscript

# Tell the dm-script the variables it should know
setvars = {"variable1": "Executed from python", "variable2": 99999}

# set your filepath, needs to be the complete path, not just the name!
path = r"C:\testdmscript4.2.s"

with execdmscript.exec_dmscript(path, setvars=setvars):
	pass
```

The variables have the values as defined in python. But there is no error, even though 
the variables were defined already. In addition, the `result()` function calls between 
the ignore markers are not executed.

#### Example 5: Multiple scripts

Sometimes it is useful to structure your dm-script code too, especially if you have bigger
files to include. You can add as many dm-scripts directly or as files as you want. Note 
that the `readvars` and the `setvars` will be defined before and after all scripts. So you 
must not use variable names in one of the scripts that are in the `setvars` and all 
variables in the `readvars` have to be delcared in exactly one file (not all `readvars` 
have to be in the same file.

Create the dm-script file `C:\testdmscript5.s` with the following content:
```c
number e = d + b;
```

Now create a new Python script with this code:
```python
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
```

#### More Examples

For more examples check out the github page. There you can find the following example 
scripts with more complicated behaviour:

- example_separate_thread.py: Show the `separate_thread` parameter of 
  `execdmscript.exec_dmscript()` by creating a progress dialog with dm-script that shows 
  the progress a python thread does
- example_combined.py: Show multiple scripts with a more complicated situation, this 
  basically takes all above scenes in one example

### One glance example

The following example shows the basic usage:

```python
try:
	from execdmscript import exec_dmscript

	# some script to execute
	script = "OKDialog(start_message)"
	script_file = "path/to/script.s"

	# variables that will be defined for the scripts (and readable later on in Python)
	sv = {"start_message": "Starting now!"}
	# variables the dm-script defines and that should be readable in the Python file
	rv = {"selected_images": list,
		"options": "TagGroup",
		"show_message": "nUmBeR"}

	with exec_dmscript(script, script_file, readvars=rv, setvars=sv) as script:
		# all variables can be accessed via indexing `script` or by using 
		# `script.synchronized_vars`, note that `script` is also iterable like a dict
		print(script["start_message"])
		print(script["selected_images"])
		print(script["options"])
		print(script["show_message"])

except Exception as e:
	# dm-script error messages only show the error type but not the message
	print("Exception: ", e)

	import traceback
	traceback.print_exc()
```

### Helper functions

`execdmscript` defines some helper functions. Those provide often used and needed 
functions related to executing dm-script code from Python.

#### Type mapping

To find the Python type for a dm-script type or the other way around, `execdmscript` 
provides the `get_dm_type()` and the `get_python_type()` functions. Both functions take 
a "type expression" and return the corresponding type in the specified language. The 
`get_dm_type()` takes a python type and returns the type for dm-script, `get_python_type()`
takes the dm-script type and returns the python type.

`get_python_type()` will return a python `type` object and take strings as arguments. 
`get_dm_type()` takes both, strings and python `type` objects and returns strings.

The following example shows the usage:

```python
import execdmscript

execdmscript.get_dm_type(int) # returns "number"
execdmscript.get_dm_type(str) # returns "string"
execdmscript.get_dm_type("text") # returns "string"
execdmscript.get_dm_type(list) # returns "TagGroup"
execdmscript.get_dm_type(dict) # returns "TagGroup"

execdmscript.get_dm_type(bool, for_taggroup=False) # returns "number"
execdmscript.get_dm_type(bool, for_taggroup=True) # returns "Boolean"

execdmscript.get_python_type("int") # returns <class 'int'>
execdmscript.get_python_type("Integer") # returns <class 'int'>
execdmscript.get_python_type("TagGroup") # returns <class 'dict'>
execdmscript.get_python_type("TagList") # returns <class 'list'>
```

The `get_dm_type()` supports the `for_taggroup` parameter. This toggles whether the 
returned string can be used in `TagGroupSetTagAs...()` or if it is the type definition to 
create a new variable in dm-script.

#### Escaping code

When creating dm-script code dynamically, which is often the case when using dm-script 
code form Python, there can be problems with escaping. For this `execdmscript` contains 
the `escape_dm_string()` function. This function escapes strings that should be included
in a string in dm-script. The `escape_dm_variable()` function escapes variable names in 
a way that they are allowed in dm-script code.

```python
import execdmscript

var = "invalid variable name"
text = """This is "a"
very
problematic text"""

var = execdmscript.escape_dm_variable(var)
text = execdmscript.escape_dm_string(text)

dm_code = "string {} = \"{}\"".format(var, text)

print(dm_code)
```

Using those two functions changes the dm-script code form (without escaping)
```C
string invalid variable name = "This is "a"
very
problematic text"
```
to the valid dm-script code
```C
string invalid_variable_name = "This is \"a\"\nvery\nproblematic text"
```

#### Converting TagGroups

To convert dm-script `TagGroup`s from and to `dict`s or `list`s, `execdmscript` offers the 
`convert_to_taggroup()` and the `convert_from_taggroup()` functions. Note that those 
functions only work with `TagGroup`s created in Python. Persistent tags are not supported.
Copying persitent tags to a local variable is not possible (GMS 3.4).

`convert_from_taggroup()` takes a `Py_TagGroup` as a parameter and returns a dict or list.
Nested `TagGroup`s are supported. The following example shows the usage:
```python
import pprint
import DigitalMicrograph as DM
import execdmscript

# create a test TagGroup
taggroup = DM.NewTagGroup()
taggroup.SetTagAsString("key1", "First text value")
taggroup.SetTagAsFloat("key2", -823.83)

taggroup2 = DM.NewTagGroup()
taggroup2.SetTagAsString("inner-key1", "Another text")
taggroup2.SetTagAsBoolean("inner-key2", False)
taggroup.SetTagAsTagGroup("key3", taggroup2)

taggroup3 = DM.NewTagList()
taggroup3.InsertTagAsText(0, "Value in list")
taggroup3.InsertTagAsText(1, "Next value in list")
taggroup3.InsertTagAsLong(2, 1234)
taggroup.SetTagAsTagGroup("key4", taggroup3)

# convert to a dict
dict_data = execdmscript.convert_from_taggroup(taggroup)
# show the converted dict
pprint.pprint(dict_data)

# convert to a list
list_data = execdmscript.convert_from_taggroup(taggroup3)
pprint.pprint(list_data)
```

`convert_to_taggroup()` is the opposite of `convert_from_taggroup()`. It takes a python
(nested) `dict` or `list` and creates a `Py_TagGroup`.

```python
import DigitalMicrograph as DM
import execdmscript

data = {
	'key1': 'First text value',
	'key2': -823.8300170898438,
	'key3': {'inner-key1': 'Another text', 'inner-key2': False},
	'key4': ['Value in list', 'Next value in list', 1234]
}

taggroup = execdmscript.convert_to_taggroup(data)

taggroup.OpenBrowserWindow(False)
```

The following code shows an example application. It allows to modify image tags by the 
user. Since `TagGroup`s cannot be travelled through in Python code, this is the only 
possibility to show the current tag structure (which is unknown because it comes from the 
camera) to the user. Adding tags shows another example for the use of 
`execdmscript.exec_dm_script()`.

```python
try:
	import time
	import pprint
	import numpy as np
	import DigitalMicrograph as DM
	import execdmscript
	
	def recordImage() -> DM.Py_Image:
		"""Record an image with the attatched camera.
		
		This is a dummy implementation and creates a random
		image with random tags.
		"""
		
		# create random data within [0..255]
		img_data = np.random.rand(64, 64)
		img_data = (img_data * 255).astype(np.uint8)

		# create Py_Image
		img = DM.CreateImage(img_data)
		# set some tags
		img.GetTagGroup().SetTagAsFloat("Acquire time", time.time())
		
		return img
	
	# record the image
	img = recordImage()
	
	# the tags to set to the image
	tags = {}
	# prepare a dialog
	dm_code = "number add_tag = TwoButtonDialog(\"Do you want to add more tags?\\nCurrent Tags:\\n{}\", \"Add Tag\", \"Done\");"
	# whether to add another tag
	add_tag = True
	while add_tag:
		# ask for the tag name and value
		tag_name = input("Please enter a tag name to add to the image")
		tag_value = input("Please enter the value for the tag '{}'".format(tag_name))
		
		tags[tag_name] = tag_value
		
		# format the current tags, escape quotes to prevent destroying the string in 
		# the dm-script code
		tag_str = execdmscript.escape_dm_string(pprint.pformat(tags))
		
		# ask whether to add another tag
		add_tag = False
		with execdmscript.exec_dmscript(dm_code.format(tag_str), readvars={"add_tag": int}) as script:
			add_tag = script["add_tag"]
	
	# convert the tags to a tag group object
	tags = execdmscript.convert_to_taggroup(tags)
	# apply the tag group object to the image
	img.GetTagGroup().DeleteAllTags()
	img.GetTagGroup().CopyTagsFrom(tags)
	
	img.ShowImage()
except Exception as e:
	# dm-script error messages only show the error type but not the message
	print("Exception: ", e)

	import traceback
	traceback.print_exc()
```

#### Remove global Tags

Sometimes it is necessary or convenient to set values to global tags. `execdmscript` 
itself makes heavy use of this. To remove the remaining global tag after performing the 
synchronization, `execdmscript` offers the `remove_global_tag()` function sice this does 
not work with plain python.

This function can be used like the following:
```python
import DigitalMicrograph as DM
import execdmscript

tagname = "new_global_tag"
DM.GetPersistentTagGroup().SetTagAsString(tagname, "test value")

# shows that the tag with the tagname exists
DM.GetPersistentTagGroup().OpenBrowserWindow(False)

execdmscript.remove_global_tag(tagname)

#  the global tag with the tagname is removed again
DM.GetPersistentTagGroup().OpenBrowserWindow(False)
```

Note that the following code **does not work**:
```python

```

### Example execution without installation

If you want to try out the module or if you don't want to install it, make sure to add the 
import path to `sys.path`. You can add the path manually:

```python
import os
import sys

# add the path to the execdmscript directory (so in execdmscript-dir there is the file 
# __init__.py and the file execdmscript.py)
sys.path.insert(0, "path/to/execdmscript-dir/")
```

If you only know the path relatively to your executing file, you can find the `__file__` 
(which does not exist in GMS) like the following code:

```python
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

import os
import sys

if __file__ != "":
	# add the parent directory to the system path so the execdmscript file
	# can be imported
	base_path = str(os.path.dirname(os.path.dirname(__file__)))
	
	if base_path not in sys.path:
		sys.path.insert(0, base_path)

import execdmscript
```

The upper code works for file structures like
```
+ base
|   + execdmscript
|   |   - __init__.py
|   |   - execdmscript.py
|   + code
|   |   - your-file-with-the-upper-code.py
```


## Installation

### Via PIP (Recommended)

You can install `execdmscript` via [PyPI](https://pypi.org/project/execdmscript/). To 
install it into the GMS virtual Python environment execute the following commands:

```cmd
conda activate GMS_VENV_Python
Python -m pip install execdmscript
```

### Manually

To manually install `execdmscript` download the `execdmscript` directory (the one that 
contains the `__init__.py` and the `execdmscript.py`) and install them

1. *Recommended if manually* in one of the GMS plugin directories by
    1. using the *File* Menu and then click on *Install Script File* 
       (Check out GMS Help in the chapter *Scripting* > *Installing Scripts and Plugins*) 
       *or*
    2. placing the `execdmscript` directory in the plugin directory manually. Plugin 
       directories are `C:\Users\UserName\AppData\Local\Gatan\Plugins` or in 
       `C:\InstallationDir\Gatan\Plugins`. To find all plugin directories execute the 
       following code:
       ```c
       string dirs = "Plugin Directories:\n\n"; 
       string dir;
       
        for(number i = 1011; i >= 1008; i--){
            try{
                dir = GetApplicationDirectory(i, 0);
                dirs += dir + "\n"
            }
            catch{
                break;
            }
        }

        result(dirs);
        OKDialog(dirs);
        ```
       *or*
1. in the miniconda plugin directory (On windows normally in 
   `%ProgramData%\Miniconda3\envs\GMS_VENV_PYTHON\Lib\site-packages`, then place the 
   `execdmscript` directory here)

## License and Publications

This module is licensed under [Mozilla Public License](https://www.mozilla.org/en-US/MPL/2.0/).

This means you can use the code for whatever you want. But please do not publish my code 
as your work.

If you want to publish papers, do so. There is no need to cite me. If you still want to 
cite me (for any reason), please contact me via Github. For any questions please also 
contact me on Github.
