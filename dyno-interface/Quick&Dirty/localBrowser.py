import tkinterweb
import tkinter as tk
import platform
import ctypes as ct
#Black bar on windows for aesthetics
def dark_title_bar(window):
    if 'Windows' in platform.platform():
        window.update()
        set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ct.windll.user32.GetParent
        hwnd = get_parent(window.winfo_id())
        value = 2
        value = ct.c_int(value)
        set_window_attribute(hwnd, 20, ct.byref(value), 4)
root = tk.Tk()
dark_title_bar(root)
root.title("Dyno Recording Interface")
frame = tkinterweb.HtmlFrame(root)
frame.load_website("http://127.0.0.1:8050/")
frame.pack(fill="both", expand=True)
root.mainloop()