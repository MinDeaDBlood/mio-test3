def append_log(text_widget, message: str):
    text_widget.insert('end', message)
    text_widget.see('end')


def clear_log(text_widget):
    text_widget.delete('1.0', 'end')
