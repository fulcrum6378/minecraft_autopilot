from pywinauto.application import Application

minecraft = Application().connect(process=8344)  # java.exe
minecraft.kill()
