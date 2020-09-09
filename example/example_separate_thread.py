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
import time
import threading

import DigitalMicrograph as DM

if __file__ != "":
	# add the parent directory to the system path so the execdmscript file
	# can be imported
	base_path = str(os.path.dirname(os.path.dirname(__file__)))
	
	if base_path not in sys.path:
		sys.path.insert(0, base_path)

from execdmscript import exec_dmscript

try:
	def do_something():
		for i in range(100):
			i += 1
			print("Progress: {}".format(i))
			DM.GetPersistentTagGroup().SetTagAsLong("__progress", i);
			time.sleep(0.05)

	thread = threading.Thread(target=do_something)
	thread.start()

	dialog_script = """
	number update_task;
	class ProgressDialog : UIFrame{
		void updateDialog(object self){
			number progress;
			if(GetPersistentTagGroup().TagGroupGetTagAsLong("__progress", progress)){
				self.DLGSetProgress("progress_bar", progress / 100);
				self.validateView();
			}
		}
		
		object init(object self){
			TagGroup Dialog = DLGCreateDialog("Dialog");

			TagGroup progress_bar = DLGCreateProgressBar("progress_bar");
			progress_bar.DLGInternalpadding(150, 0);

			Dialog.DLGAddElement(progress_bar);
			update_task = AddMainThreadPeriodicTask(self, "updateDialog", 0.1);
			
			self.super.init(Dialog);
			return self;
		}
	}
	// do not move this in the thread part, this will not work anymore
	object progress_dlg = alloc(ProgressDialog).init();
	
	"""
	exec_script = """
	if(!GetPersistentTagGroup().TagGroupDoesTagExist("__progress")){
		GetPersistentTagGroup().TagGroupCreateNewLabeledTag("__progress");
		GetPersistentTagGroup().TagGroupSetTagAsLong("__progress", 0);
	}
	
	progress_dlg.pose();
	
	if(GetPersistentTagGroup().TagGroupDoesTagExist("__progress")){
		GetPersistentTagGroup().TagGroupDeleteTagWithLabel("__progress");
	}
	RemoveMainThreadTask(update_task);
	"""
	with exec_dmscript(dialog_script, separate_thread=(exec_script, ), debug=False) as script:
		pass
		
	thread.join()
except Exception as e:
	# dm-script error messages are very bad, use this for getting the error text and the 
	# correct traceback
	print("Exception: ", e)
	import traceback
	traceback.print_exc()