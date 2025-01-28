import webview
import platform
import ctypes as ct
import pygetwindow as gw
import subprocess



def open_browser():

    # Open the WebView inside the Tkinter window
    window = webview.create_window('Dyno Recording Interface', 'http://127.0.0.1:8050/',maximized=True)
    
    window.background_color = '#000000'
    
    # Start the webview
    webview.start()
    
    #dark_title_bar(window)
process = subprocess.Popen(["python",r'dyno-interface\\Quick&Dirty\\hackBrowser.py'])
open_browser()
process.kill()


