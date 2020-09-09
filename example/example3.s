
TagGroup dlg, dlg_items, wrapper, inputs;

dlg = DLGCreateDialog("Add text to the headlines", dlg_items);
wrapper = DLGCreateGroup();
wrapper.DLGTableLayout(2, headlines.TagGroupCountTags(), 0);

inputs = NewTagList();
for(number i = 0; i < headlines.TagGroupCountTags(); i++){
	string text;
	if(headlines.TagGroupGetIndexedTagAsString(i, text)){
		TagGroup label = DLGCreateLabel("Text for " + text, 25);
		wrapper.DLGAddElement(label);
		
		TagGroup input = DLGCreateStringField("");
		input.DLGIdentifier("input-" + i);
		wrapper.DLGAddElement(input);
		inputs.TagGroupInsertTagAsTagGroup(infinity(), input);
	}
}

dlg.DLGAddElement(wrapper);

object dialog = alloc(UIFrame).init(dlg);

// make sure the variable always exists, it may be empty but 
// it has to be declared!
TagGroup headline_texts = NewTagList();

if(dialog.pose()){
	for(number i = 0; i < headlines.TagGroupCountTags(); i++){
		string text;
		if(headlines.TagGroupGetIndexedTagAsString(i, text)){
			TagGroup input;
			inputs.TagGroupGetIndexedTagAsTagGroup(i, input);
			
			TagGroup vals = NewTagGroup();
			vals.TagGroupCreateNewLabeledTag("headline");
			vals.TagGroupSetTagAsString("headline", text);
			
			vals.TagGroupCreateNewLabeledTag("text");
			vals.TagGroupSetTagAsString("text", input.DLGGetStringValue());
			
			headline_texts.TagGroupInsertTagAsTagGroup(infinity(), vals);
		}
	}
}