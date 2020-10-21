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