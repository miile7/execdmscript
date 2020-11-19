import execdmscript

# get a tag value by the path with : as a separator
program_name = execdmscript.get_persistent_tag("Private:Configuration:ApplicationName")
# get a tag value by using a tuple with the path components
program_version = execdmscript.get_persistent_tag(("Private", "Configuration", "ApplicationVersion_2"))
print("This is {} with version {}.".format(program_name, program_version))

# get another value
print("The current save path is {}.".format(execdmscript.get_persistent_tag("Private:Current Directory")))

# get a TagGroup which is automatically converted to a dict
settings_dict = execdmscript.get_persistent_tag("Private:CreateNewDialog")
print("When creating a new image, the following settings apply:")
for name, val in settings_dict.items():
	print("  {}: {}".format(name, val))

# when the tag does not exist, a KeyError is raised
try:
	execdmscript.get_persistent_tag("This:persistent:tag:does:not:exist")
except KeyError as e:
	print("This tag does not exist: {}".format(e))