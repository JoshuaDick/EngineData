import platform
import ctypes as ct
import pygetwindow as gw
import time

def dark_title_bar_hacky():
    if 'Windows' in platform.platform():
        #keep trying every 100ms
        while (len(gw.getWindowsWithTitle('Dyno Recording Interface')) == 0):
            a = 1
            time.sleep(0.1)
        hwnd = gw.getWindowsWithTitle('Dyno Recording Interface')[0]._hWnd
        

        # Apply dark mode to the title bar (2 is for dark mode, 20 is the attribute identifier)
        set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        value = ct.c_int(2)  # 2 is for dark mode
        set_window_attribute(hwnd, 20, ct.byref(value), 4)


dark_title_bar_hacky()