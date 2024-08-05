import copy
import ctypes
import locale
import time
import warnings

# noinspection PyUnresolvedReferences
import pywintypes
import six
import win32api
# noinspection PyUnresolvedReferences
import win32con
import win32gui
from pywinauto import win32functions, Application, keyboard, win32defines
from pywinauto.controls.hwndwrapper import DialogWrapper


# open notepad and make it push a button continually...

def send_my_keys(w,
                 keystrokes,
                 with_spaces=True,
                 with_tabs=True,
                 with_newlines=True):
    """
    Silently send keystrokes to the control in an inactive window

    It parses modifiers Shift(+), Control(^), Menu(%) and Sequences like "{TAB}", "{ENTER}"
    For more information about Sequences and Modifiers navigate to module `keyboard`_

    .. _`keyboard`: pywinauto.keyboard.html

    Due to the fact that each application handles input differently and this method
    is meant to be used on inactive windows, it may work only partially depending
    on the target app. If the window being inactive is not essential, use the robust
    `type_keys`_ method.

    .. _`type_keys`: pywinauto.base_wrapper.html#pywinauto.base_wrapper.BaseWrapper.type_keys
    """
    PBYTE256 = ctypes.c_ubyte * 256

    win32gui.SendMessage(w, win32con.WM_ACTIVATE,
                         win32con.WA_ACTIVE, 0)
    target_thread_id = win32functions.GetWindowThreadProcessId(w, None)
    current_thread_id = win32functions.GetCurrentThreadId()
    attach_success = win32functions.AttachThreadInput(target_thread_id, current_thread_id, True) != 0
    if not attach_success:
        warnings.warn('Failed to attach app\'s thread to the current thread\'s message queue',
                      UserWarning, stacklevel=2)

    keyboard_state_stack = [PBYTE256()]
    win32functions.GetKeyboardState(keyboard_state_stack[-1])

    input_locale_id = win32functions.GetKeyboardLayout(0)
    context_code = 0

    keys = keyboard.parse_keys(keystrokes, with_spaces, with_tabs, with_newlines)
    key_combos_present = any([isinstance(k, keyboard.EscapedKeyAction) for k in keys])
    if key_combos_present:
        warnings.warn('Key combinations may or may not work depending on the target app',
                      UserWarning, stacklevel=2)

    try:
        for key in keys:
            vk, scan, flags = key.get_key_info()

            if vk == keyboard.VK_MENU or context_code == 1:
                down_msg, up_msg = win32con.WM_SYSKEYDOWN, win32con.WM_SYSKEYUP
            else:
                down_msg, up_msg = win32con.WM_KEYDOWN, win32con.WM_KEYUP

            repeat = 1
            shift_state = 0
            unicode_codepoint = flags & keyboard.KEYEVENTF_UNICODE != 0
            if unicode_codepoint:
                char = chr(scan)
                vk_with_flags = win32functions.VkKeyScanExW(char, input_locale_id)
                vk = vk_with_flags & 0xFF
                shift_state = (vk_with_flags & 0xFF00) >> 8
                scan = win32functions.MapVirtualKeyW(vk, 0)

            if key.down and vk > 0:
                new_keyboard_state = copy.deepcopy(keyboard_state_stack[-1])

                new_keyboard_state[vk] |= 128
                if shift_state & 1 == 1:
                    new_keyboard_state[keyboard.VK_SHIFT] |= 128
                # NOTE: if there are characters with CTRL or ALT in the shift
                # state, make sure to add these keys to new_keyboard_state

                keyboard_state_stack.append(new_keyboard_state)

                lparam = (
                        repeat << 0 |
                        scan << 16 |
                        (flags & 1) << 24 |
                        context_code << 29 |
                        0 << 31)

                win32functions.SetKeyboardState(keyboard_state_stack[-1])
                win32functions.PostMessage(w, down_msg, vk, lparam)
                if vk == keyboard.VK_MENU:
                    context_code = 1

                # a delay for keyboard state to take effect
                time.sleep(0.01)

            if key.up and vk > 0:
                keyboard_state_stack.pop()

                lparam = (
                        repeat << 0 |
                        scan << 16 |
                        (flags & 1) << 24 |
                        context_code << 29 |
                        1 << 30 |
                        1 << 31)

                win32functions.PostMessage(w, up_msg, vk, lparam)
                win32functions.SetKeyboardState(keyboard_state_stack[-1])

                if vk == keyboard.VK_MENU:
                    context_code = 0

                # a delay for keyboard state to take effect
                time.sleep(0.01)

    except pywintypes.error as e:
        if e.winerror == 1400:
            warnings.warn('Application exited before the end of keystrokes',
                          UserWarning, stacklevel=2)
        else:
            warnings.warn(e.strerror, UserWarning, stacklevel=2)
        win32functions.SetKeyboardState(keyboard_state_stack[0])

    if attach_success:
        win32functions.AttachThreadInput(target_thread_id, current_thread_id, False)


def type_my_keys(
        w,
        keys,
        pause=None,
        with_spaces=False,
        with_tabs=False,
        with_newlines=False,
        turn_off_numlock=True,
        set_foreground=True,
        vk_packet=True):
    """
    Type keys to the element using keyboard.send_keys

    This uses the re-written keyboard_ python module where you can
    find documentation on what to use for the **keys**.

    .. _keyboard: pywinauto.keyboard.html
    """
    w.verify_actionable()
    friendly_class_name = w.friendly_class_name()

    if pause is None: pause = .01

    # if set_foreground:
    #    w.set_focus()

    # attach the Python process with the process that self is in
    if w.element_info.handle:
        window_thread_id = win32functions.GetWindowThreadProcessId(w.handle, None)
        win32functions.AttachThreadInput(win32functions.GetCurrentThreadId(), window_thread_id, win32defines.TRUE)
        # TO-DO: check return value of AttachThreadInput properly
    else:
        # TO-DO: UIA stuff maybe
        pass

    if isinstance(keys, six.text_type):
        aligned_keys = keys
    elif isinstance(keys, six.binary_type):
        aligned_keys = keys.decode(locale.getpreferredencoding())
    else:
        # convert a non-string input
        aligned_keys = six.text_type(keys)

    # Play the keys to the active window
    keys = keyboard.parse_keys(
        keys, with_spaces, with_tabs, with_newlines,
        vk_packet=vk_packet)

    for k in keys:
        k.run()
        time.sleep(pause)

    # detach the python process from the window's process
    if w.element_info.handle:
        win32functions.AttachThreadInput(win32functions.GetCurrentThreadId(), window_thread_id, win32defines.FALSE)
        # TO-DO: check return value of AttachThreadInput properly
    else:
        # TO-DO: UIA stuff
        pass

    w.wait_for_idle()

    # w.actions.log('Typed text to the ' + friendly_class_name + ': ' + aligned_keys)
    return w


app = Application(backend="uia").start("notepad.exe")
dw: DialogWrapper = app.top_window().wrapper_object()
# dw.set_focus()
# print(dw.handle)
type_my_keys(dw, "FUCK")
# time.sleep(1)
# win32gui.SendMessage(dw.handle, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
# win32functions.PostMessage(dw.handle, win32con.WM_CHAR, ord('F'), 0)
# win32gui.SendMessage(dw.handle, win32con.WM_KEYDOWN, 0x41, 0x1E0001)
# win32api.keybd_event()
time.sleep(1)
# win32gui.SendMessage(dw.handle, win32con.WM_KEYUP, win32con.VK_ESCAPE, 0)
# win32functions.PostMessage(dw.handle, win32con.WM_CHAR, ord('F'), 0)
# dw.send_message(win32con.WM_CHAR, ord('F'), 0)
# send_my_keys(dw.handle, "F")
# win32functions.PostMessage(dw.handle, win32con.WM_CHAR, ord('F'), 0)
# win32gui.SendMessage(dw.handle, win32con.WM_KEYUP, 0x41, 0x1E0001)
time.sleep(2)
# dw.type_keys("%FX")
win32gui.SendMessage(dw.handle, win32con.WM_CLOSE)
