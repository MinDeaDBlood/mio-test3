def bind_drop_target(widget, callback):
    from src.ui.common.dnd import DND_FILES

    widget.drop_target_register(DND_FILES)
    widget.dnd_bind('<<Drop>>', callback)
    return widget
