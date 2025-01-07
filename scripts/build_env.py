import sys
import os
from platform import system as sysname

envs = {
    "CALIBRE_RESOURCES_PATH": sys.resources_location,
    "CALIBRE_EXTENSIONS_PATH": sys.extensions_location,
}

if sysname() in ["Linux", "Darwin"]:
    envs["CALIBRE_LIBRARY_PATH"] = ":".join(
        set(os.getenv("LD_LIBRARY_PATH").split(":"))
    )


with open(".env", "w+") as f:
    for name, value in envs.items():
        f.write(f"{name}={value}\n")
