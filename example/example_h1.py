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