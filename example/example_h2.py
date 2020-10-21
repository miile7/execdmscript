import execdmscript

var = "invalid variable name"
text = """This is "a"
very
problematic text"""

# var = execdmscript.escape_dm_variable(var)
# text = execdmscript.escape_dm_string(text)

dm_code = "string {} = \"{}\"".format(var, text)

print(dm_code)