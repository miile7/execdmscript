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