from time import sleep
from pywinauto.application import Application

app = Application(backend="uia").start("notepad.exe")
app.UntitledNotepad.type_keys("FUCK-YOU")
sleep(3)
app.UntitledNotepad.type_keys("%FX")
