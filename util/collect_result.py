import os
import re


def Read(path):
    try:
        with open(path, "rb") as f:
            return f.read().strip()
    except:
        return b"None"


results = {}

SCRATCH_DIR = ""
DELIMITER = "XXXX"

for i in range(3):
    if os.path.exists("../" * i + "firmae.config"):
        SCRATCH_DIR = "../" * i + "scratch"

for roots, dirs, files in os.walk(SCRATCH_DIR):
    for iid in dirs:
        path = os.path.join(SCRATCH_DIR, iid)
        brand = Read(os.path.join(path, "brand")).decode()
        name = Read(os.path.join(path, "name")).decode()
        arch = Read(os.path.join(path, "architecture")).decode()
        ip = Read(os.path.join(path, "ip")).decode()
        ping = Read(os.path.join(path, "ping")).decode()
        web = Read(os.path.join(path, "web")).decode()

        rce_data = Read(os.path.join(path, "qemu.final.serial.log"))
        rces = re.findall(b": echo (b33f\w+)", rce_data)
        if rces:
            rces = list(map(lambda x: x.decode(), rces))

        info_data = Read(os.path.join(path, "analysis_log", "rsf")).decode()
        infos = re.findall("(b33f\w+)", info_data)
        rces.extend(infos)
        if rces:
            rces = sorted(set(rces))
            rces = ",".join(rces)
        else:
            rces = "None"

        results[int(iid)] = DELIMITER.join(
            [iid, brand, name, arch, ip, ping, web, rces]
        )
    break

titles = DELIMITER.join(["Number", "Brand", "Name", "Arch", "IP", "Ping", "Web", "RCE"])

outfile = open("result.txt", "w")
outfile.write(titles + "\n")
for i in sorted(results):
    outfile.write(results[i] + "\n")

outfile.close()
