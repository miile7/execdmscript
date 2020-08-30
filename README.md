# execdmscript

A python module for executing DM-Script from python in 
[Gatan Microscopy Suite® (GMS) (Digital Micrograph)](https://www.gatan.com/products/tem-analysis/gatan-microscopy-suite-software).

**Table of Contents**

1. [Foreword](#foreword)
2. [Usage](#usage)
3. [Installation](#installation)
4. [License and Publications](#license-and-publications)

## Foreword

This module is created because I needed to use DM-Scripts Dialogs in my project. But this
project was written in python. Because there is no python implementation for dialogs I 
decided to execute DM-Script that creates the dialogs. But then getting data from one to
the other programming language was more difficult than I thought. This module tries to 
solve those problems and hide verything away.

## Usage

The module can oly be used inside Gatan Microscopy Suite®. The following example shows the
basic usage:
```python
from execdmscript import exec_dmscript

# some script to execute
script = "OKDialog(start_message)"
script_file = "path/to/script.s"

# variables that will be defined for the scripts (and readable later on in python)
sv = {"start_message": "Starting now!"}
# variables the dm-script defines and that should be readable in the python file
rv = {"selected_images": list,
      "options": "TagGroup",
      "show_message": "nUmBeR"}

with exec_dmscript(script, script_file, readvars=rv, setvars=sv) as script:
    print(script["start_message"])
    print(script["selected_images"])
    print(script["options"])
    print(script["show_message"])

    # all variables can be accessed via indexing `script` or by using 
    # `script.synchronized_vars`, note that `script` is also iterable like a dict
```

Note that the upper script only runs when `execdmscript` is installed in one of the 
Gatan Microscopy Suite® plugins directories or in the miniconda installation coming with
GMS.

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

You can install `execdmscript` via [PyPI](https://pypi.org/) by running

```cmd
pip install execdmscript
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
