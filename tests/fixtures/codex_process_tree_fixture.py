import subprocess
import sys
import time
from pathlib import Path


pid_file = Path(sys.argv[1])
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)"])
pid_file.write_text(str(child.pid), encoding="utf-8")
while True:
    time.sleep(1)
