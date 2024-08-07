import ctypes
import json
import sys
from subprocess import Popen
from time import sleep

import minecraft_launcher_lib
import win32api
# noinspection PyUnresolvedReferences
import win32con
import win32gui
import win32ui
from PIL import ImageGrab, Image
from pywinauto.application import Application, WindowSpecification
from pywinauto.controls.hwndwrapper import DialogWrapper
from pywinauto.timings import Timings

KEYEVENTF_KEYDOWN = 0x0000


def enter():
    global w
    w.set_focus()
    w.move_mouse(coords=(435, 160))
    w.click()
    sleep(2)


def move(direction: int, length: int = 5, sit: bool = False):
    key = {
        0: 87,  # W
        1: 68,  # D
        2: 83,  # S
        3: 65,  # A
    }[direction]
    if sit:
        ctypes.windll.user32.keybd_event(win32con.VK_LSHIFT, 0, KEYEVENTF_KEYDOWN, 0)
    ctypes.windll.user32.keybd_event(key, 0, KEYEVENTF_KEYDOWN, 0)
    sleep(length)
    ctypes.windll.user32.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
    if sit:
        ctypes.windll.user32.keybd_event(win32con.VK_LSHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)


def jump():
    ctypes.windll.user32.keybd_event(win32con.VK_SPACE, 0, KEYEVENTF_KEYDOWN, 0)
    sleep(.5)  # it won't work if you release the key immediately!
    ctypes.windll.user32.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)


def screenshot(rect=None):
    global w
    w.set_focus()
    control_rectangle = w.rectangle()
    if not (control_rectangle.width() and control_rectangle.height()):
        return None

    # PIL is optional so check first
    if not ImageGrab:
        print("PIL does not seem to be installed. "
              "PIL is required for capture_as_image")
        w.actions.log("PIL does not seem to be installed. "
                      "PIL is required for capture_as_image")
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
w.set_focus()
sleep(20)
w.move_mouse(coords=(435, 235))
w.click()
sleep(1)
w.move_mouse(coords=(435, 175))
w.click()
w.move_mouse(coords=(400, 400))
w.click()
sleep(60)
print('Listening for user input.....')

while True:
    try:
        exe = input()
        enter()
        exec(exe)
    except Exception as e:
        print(str(type(e)) + ':', e)

    # import pywinauto.mouse as mouse
    # mouse.move(coords=(435, 265))
