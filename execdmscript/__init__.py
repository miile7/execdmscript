"""A python module to use inside Gatan Microscopy Suite (GMS). It offers to 
exeucte dm-scripts directly or saved in files. In addition you can define 
variables that will passed to the dm-script and get the values of variables set 
in the executed dm-script.

You can add multiple files and scripts. The scripts will be appended to one big 
file and then executed in the same order. To debug those files use the `debug` 
option.

Usage:
```python
>>> prefix = "\n".join((
...     "string command = \"select-image\";",
...     "number preselected_image = {};".format(show_image)
... ))
>>> # those values will be accessable if they are defined in the dm-script
>>> rv = {"sel_img_start": "Integer",
...         "sel_img_end": int,
...         "options": str}
>>> # those values will be accessable in dm-script (and later in python)
>>> sv = {"a": 20}
>>> with exec_dmscript(prefix, filepath, readvars=rv, setvars=sv) as script:
...     for k in script.synchronized_vars:
...         # show the variables value
...         print("Variable {} has the value {}".format(k, script[k]))
...         # script[k] is equal to script.synchronized_vars[k]
```

This uses the persistent tags to communicate from dm-script to python.

Note that this is not thread-safe!
"""

from .execdmscript import *

__version__ = "1.1.6"