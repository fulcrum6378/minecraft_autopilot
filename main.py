import json
import minecraft_launcher_lib
import subprocess
import sys

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


prc = subprocess.run(minecraft_command)
sys.exit(prc.returncode)

# minecraft = Application().start(' '.join(minecraft_command))
# pywintypes.error: (1471, 'WaitForInputIdle',
# 'Unable to finish the requested operation because the specified process is not a GUI process.')
