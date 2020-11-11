import DigitalMicrograph as DM
import execdmscript

tagname = "new_global_tag"
DM.GetPersistentTagGroup().SetTagAsString(tagname, "test value")

# shows that the tag with the tagname exists
DM.GetPersistentTagGroup().OpenBrowserWindow(False)

execdmscript.remove_global_tag(tagname)

#  the global tag with the tagname is removed again
DM.GetPersistentTagGroup().OpenBrowserWindow(False)