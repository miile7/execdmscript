TagGroup dlg, dlg_items, field;

dlg = DLGCreateDialog("Headlines of website", dlg_items);

field = DLGCreateLabel(text);
field.DLGWidth(100);
field.DLGHeight(4);

dlg.DLGAddElement(field);

alloc(UIFrame).init(dlg).pose();