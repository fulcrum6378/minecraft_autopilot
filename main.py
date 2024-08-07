import ctypes
import json
import sys
from ctypes.wintypes import LPARAM, POINT, RECT, UINT
from subprocess import Popen
from time import sleep

import minecraft_launcher_lib
import win32api
import win32con
import win32gui
import win32ui
from PIL import Image, ImageGrab
from pywinauto.application import Application, WindowSpecification
from pywinauto.controls.hwndwrapper import DialogWrapper
from pywinauto.timings import Timings
from win32con import (KEYEVENTF_KEYUP, VK_LCONTROL, VK_LSHIFT, VK_SPACE,
                      WM_LBUTTONDOWN, WM_LBUTTONUP, WM_RBUTTONDOWN, WM_RBUTTONUP, WM_MOUSEMOVE)

GetWindowPlacement = ctypes.windll.user32.GetWindowPlacement
ShowWindow = ctypes.windll.user32.ShowWindow
PostMessage = ctypes.windll.user32.PostMessageW
keybd_event = ctypes.windll.user32.keybd_event
KEYEVENTF_KEYDOWN = 0x0000


class WindowPlacement(ctypes.Structure):
    _fields_ = [
        ('length', UINT),
        ('flags', UINT),
        ('showCmd', UINT),
        ('ptMinPosition', POINT),
        ('ptMaxPosition', POINT),
        ('rcNormalPosition', RECT),
    ]


def focus():
    global w
    wp = WindowPlacement()
    wp.length = ctypes.sizeof(wp)
    ret = GetWindowPlacement(w, ctypes.byref(wp))
    if not ret: raise ctypes.WinError()
    if wp.showCmd == win32con.SW_SHOWMINIMIZED:
        ShowWindow(w,
                   win32con.SW_MAXIMIZE if wp.flags & win32con.WPF_RESTORETOMAXIMIZED == win32con.WPF_RESTORETOMAXIMIZED
                   else win32con.SW_RESTORE)
    else:
        win32gui.ShowWindow(w.handle, win32con.SW_SHOW)
    win32gui.SetForegroundWindow(w.handle)
    sleep(.06)


def click(x: int = 0, y: int = 0):
    global w
    if x != 0 or y != 0:
        PostMessage(w, WM_MOUSEMOVE, 0, LPARAM(((y & 0xFFFF) << 16) | (x & 0xFFFF)))
        sleep(.01)
    PostMessage(w, WM_LBUTTONDOWN, 0, 0)
    sleep(.01)
    PostMessage(w, WM_LBUTTONUP, 0, 0)
    sleep(.1)


def enter():
    focus()
    click(435, 160)
    sleep(2)


def look():
    pass  # TODO


def move(direction: int, length: int = 5, sneak: bool = False, sprint: bool = False):
    key = {
        0: 87,  # W
        1: 68,  # D
        2: 83,  # S
        3: 65,  # A
    }[direction]
    if sneak:
        keybd_event(VK_LSHIFT, 0, KEYEVENTF_KEYDOWN, 0)
    if sprint:
        keybd_event(VK_LCONTROL, 0, KEYEVENTF_KEYDOWN, 0)
    keybd_event(key, 0, KEYEVENTF_KEYDOWN, 0)
    sleep(length)
    keybd_event(key, 0, KEYEVENTF_KEYUP, 0)
    if sneak:
        keybd_event(VK_LSHIFT, 0, KEYEVENTF_KEYUP, 0)
    if sprint:
        keybd_event(VK_LCONTROL, 0, KEYEVENTF_KEYUP, 0)


def jump():
    keybd_event(VK_SPACE, 0, KEYEVENTF_KEYDOWN, 0)
    sleep(.5)  # it won't work if you release the key immediately!
    keybd_event(VK_SPACE, 0, KEYEVENTF_KEYUP, 0)


def attack(length: int = 5):
    global w
    PostMessage(w, WM_LBUTTONDOWN, 0, 0)
    sleep(length)
    PostMessage(w, WM_LBUTTONUP, 0, 0)
    sleep(.1)


def use(length: int = 5):
    global w
    PostMessage(w, WM_RBUTTONDOWN, 0, 0)
    sleep(length)
    PostMessage(w, WM_RBUTTONUP, 0, 0)
    sleep(.1)


def screenshot(rect=None):
    global w
    focus()
    control_rectangle = w.rectangle()
    if not (control_rectangle.width() and control_rectangle.height()):
        return None
    if rect: control_rectangle = rect

    # get the control rectangle in a way that PIL likes it
    width = control_rectangle.width()
    height = control_rectangle.height()
    left = control_rectangle.left
    right = control_rectangle.right
    top = control_rectangle.top
    bottom = control_rectangle.bottom
    box = (left, top, right, bottom)

    # check the number of monitors connected
    # noinspection PyUnresolvedReferences
    if (sys.platform == 'win32') and (len(win32api.EnumDisplayMonitors()) > 1):
        hwin = win32gui.GetDesktopWindow()
        hwin_dc = win32gui.GetWindowDC(hwin)
        src_dc = win32ui.CreateDCFromHandle(hwin_dc)
        mem_dc = src_dc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(src_dc, width, height)
        mem_dc.SelectObject(bmp)
        mem_dc.BitBlt((0, 0), (width, height), src_dc, (left, top), win32con.SRCCOPY)

        bmp_info = bmp.GetInfo()
        bmp_str = bmp.GetBitmapBits(True)
        # noinspection SpellCheckingInspection
        pil_img_obj = Image.frombuffer(
            'RGB', (bmp_info['bmWidth'], bmp_info['bmHeight']),
            bmp_str, 'raw', 'BGRX', 0, 1)
    else:
        # grab the image and get raw data as a string
        pil_img_obj = ImageGrab.grab(box)

    pil_img_obj.save('screenshot.png')


# prepare Minecraft
minecraft_directory = 'D:\\Games\\Minecraft'
uc = json.loads(open(minecraft_directory + '\\usercache.json', 'r').read())
lp = json.loads(open(minecraft_directory + '\\launcher_profiles.json', 'r').read())
options: minecraft_launcher_lib.types.MinecraftOptions = {
    # mandatory:
    'username': uc[0]['name'],
    'uuid': uc[0]['uuid'],
    'token': lp['clientToken'],
    # optional:
    'executablePath': 'C:\\Users\\fulcr\\AppData\\Local\\Programs\\JDK-21.0.2\\bin\\java.exe',
    'gameDirectory': minecraft_directory,
}
minecraft_command: list[str] = (
    minecraft_launcher_lib.command.get_minecraft_command('1.20.6', minecraft_directory, options))
del uc, lp, options

# start the process and connect to it
process: Popen = Popen(minecraft_command)
minecraft: Application = Application().connect(process=process.pid)  # java.exe

# prepare the game
Timings.slow()
Timings.window_find_timeout = 80
window: WindowSpecification = minecraft.top_window()  # blocks until the window is created
window.wait('ready')
sleep(5)
w: DialogWrapper = window.wrapper_object()
sleep(15)
focus()
click(435, 235)
sleep(1)
click(435, 175)
click(400, 400)
sleep(60)
print('Listening for user input.....')

while True:
    try:
        exe = input()
        enter()
        exec(exe)
    except Exception as e:
        print(str(type(e)) + ':', e)
