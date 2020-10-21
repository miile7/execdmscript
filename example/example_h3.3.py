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
		
		tag_str = execdmscript.escape_dm_string(pprint.pformat(tags))
		print(tag_str)
		
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