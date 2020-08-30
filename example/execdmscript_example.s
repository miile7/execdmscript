number index;
TagGroup tg1 = NewTagGroup();
index = tg1.TagGroupCreateNewLabeledTag("key1");
tg1.TagGroupSetIndexedTagAsString(index, "value1");

index = tg1.TagGroupCreateNewLabeledTag("key2");
// c is defined in the inline script loaded before
tg1.TagGroupSetIndexedTagAsNumber(index, c);

TagGroup tl1 = NewTagList();
tl1.TagGroupInsertTagAsString(infinity(), "list value 1");
tl1.TagGroupInsertTagAsString(infinity(), "list value 2");
tl1.TagGroupInsertTagAsNumber(infinity(), 100);

TagGroup tg2 = NewTagGroup();
index = tg2.TagGroupCreateNewLabeledTag("list");
tg2.TagGroupSetIndexedTagAsTagGroup(index, tl1);
index = tg2.TagGroupCreateNewLabeledTag("list-count");
tg2.TagGroupSetIndexedTagAsNumber(index, tl1.TagGroupCountTags());

index = tg1.TagGroupCreateNewLabeledTag("key3");
tg1.TagGroupSetIndexedTagAsTagGroup(index, tg2);

index = tg1.TagGroupCreateNewLabeledTag("key4");
tg1.TagGroupSetIndexedTagAsBoolean(index, 0);