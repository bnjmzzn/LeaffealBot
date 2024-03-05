import os
import sys
from time import sleep

print(f"[restarting] {sys.argv[1]}")
sleep(1)
os.system("python ./main.py")