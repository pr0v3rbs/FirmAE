#!/usr/bin/env python3

import sys
import threading
import subprocess as sp
import time
import os
import signal
import scripts.util as util
import multiprocessing as mp
import logging, coloredlogs
coloredlogs.install(level=logging.DEBUG)
coloredlogs.install(level=logging.INFO)
#rootLogger = logging.getLogger()
#rootLogger.setLevel(logging.DEBUG)


class docker_helper:
    def __init__(self, firmae_root, remove_image=False):
        self.firmae_root = firmae_root
        self.count = 0
        self.last_core = None
        self.__sync_status()
        self.remove_image = remove_image

    def __sync_status(self):
        containers = self.get_container_list(with_pause=True)
        self.count = len(containers)
        logging.debug("[*] current core : {}".format(self.count))

    def get_container_list(self, with_pause=False):
        lines = sp.check_output("docker ps", shell=True).decode().split('\n')[1:-1]
        ret = []
        for line in lines:
            if not with_pause and line.find("Paused") != -1:
                continue
            ret.append(line.split(" ")[-1])

        return ret[::-1]

    def stop_core(self, container_name):
        return sp.check_output("docker stop {}".format(container_name), shell=True)

    def run_core(self, idx, mode, brand, firmware_path):
        firmware_root = os.path.dirname(firmware_path)
        firmware = os.path.basename(firmware_path)
        docker_name = 'docker{}_{}'.format(idx, firmware)
        cmd = """docker run -dit --rm \\
                -v /dev:/dev \\
                -v {0}:/work/FirmAE \\
                -v {1}:/work/firmwares \\
                --privileged=true \\
                --name {2} \\
                fcore""".format(self.firmae_root,
                                firmware_root,
                                docker_name)

        sp.check_output(cmd, shell=True)
        logging.info("[*] {} emulation start!".format(docker_name))
        time.sleep(5)

        docker_mode = "-it" if mode == "-d" else "-id"
        cmd = "docker exec {0} \"{1}\" ".format(docker_mode, docker_name)
        cmd += "bash -c \"cd /work/FirmAE && "
        cmd += "./run.sh {0} {1} /work/firmwares/{2} ".format(mode,
                                                              brand,
                                                              firmware)
        if mode == "-d":
            cmd += "\""
        else:
            cmd += "2>&1 > /work/FirmAE/scratch/{0}.log\" &".format(firmware)

        t0 = time.time()
        iid = -1
        if mode == "-d":
            os.system(cmd)
        else:
            sp.check_output(cmd, shell=True)
        firmware_log = os.path.join(self.firmae_root, "scratch", firmware + ".log")

        if mode == "-r":
            cmd = "docker exec -it \"{0}\" bash".format(docker_name)
            os.system(cmd)

        if mode in ["-r", "-d"]:
            return docker_name

        time.sleep(10)
        while iid == -1:
            time.sleep(1)
            iid = util.get_iid(firmware_path, "127.0.0.1")
            with open(firmware_log) as f:
                f.readline()
                last_line = f.readline()
                if last_line.find("container failed") != -1:
                    logging.error("[-] %s container failed to connect to the hosts' postgresql".format(docker_name))
                    return docker_name

        if not iid:
            logging.error("[-] %s getting iid failed.", docker_name)
            return docker_name

        # check success of extractor
        tgz_path = os.path.join(self.firmae_root, "images", str(iid) + ".tar.gz")
        for i in range(300):
            time.sleep(1)
            if os.path.exists(tgz_path):
                break
        else:
            logging.error("[-] %s extraction failed.", docker_name)
            return docker_name

        # check
        emulation_result = self.check_result(firmware, docker_name, brand, iid, True)
        time_elapsed = time.time() - t0

        work_dir = os.path.join(self.firmae_root, "scratch", str(iid))
        if os.path.exists(work_dir):
            with open(os.path.join(work_dir, 'time_elapsed'), 'w') as f:
                f.write("%0.4f\n" % (time_elapsed))

            os.rename(os.path.join(self.firmae_root, 'scratch',
                                   "{0}.log".format(firmware)),
                      os.path.join(work_dir, "{0}.log".format(firmware)))

            with open(os.path.join(work_dir, 'fullname'), 'w') as f:
                f.write("%s\n" % (firmware_path))

            if self.remove_image:
                image_name = os.path.join(work_dir, 'image.raw')
                if os.path.exists(image_name):
                    os.remove(image_name)

        if emulation_result:
            logging.info("[+] %s emulation finished. (%0.4fs)", docker_name, time_elapsed)

            # analyses
            if mode == "-a":
                t1 = time.time()
                analyses_result = self.check_result(firmware, docker_name, brand, iid, False)
                time_elapsed = time.time() - t1

                if analyses_result:
                    logging.info("[+] %s analysis finished. (%0.4fs)", docker_name, time_elapsed)
                else:
                    logging.error("[-] %s analysis failed. (%0.4fs)", docker_name, time_elapsed)

        else:
            logging.error("[-] %s emulation failed. (%0.4fs)", docker_name, time_elapsed)

        return docker_name

    def run_command(self, core, cmd):
        result = '[-] failed'
        try:
            result = sp.check_output('docker exec -it {} bash -c "{}"'.format(core, cmd), shell=True).decode()
        except:
            pass

        return result

    def run_script(self, core, script):
        result = '[-] failed'
        try:
            sp.check_output('docker cp {} {}:/'.format(script, core), shell=True)
            result = sp.check_output('docker exec -it {} /{}'.format(core, script), shell=True).decode()
        except:
            pass

        return result

    def check_result(self, firmware, docker_name, brand, iid, is_emulation=True):
        time.sleep(10) # wait until re-run
        if is_emulation:
            result_path = "{}/scratch/{}/result".format(self.firmae_root, iid)
            timeout = 2400
        else:
            result_path = "{}/analyses/analyses_log/{}/{}/result".format(self.firmae_root, brand, iid)
            timeout = 3600

        for i in range(timeout):
            time.sleep(1)

            if not os.path.exists(result_path):
                continue

            with open(result_path) as f:
                result = f.read().strip()
                if result == "true":
                    return True
                else:
                    return False

        return False

    def get_docker_tap_ip(self, docker_name):
        result = 'None'
        try:
            result = sp.check_output('docker exec -it {} bash -c "ip route"'.format(docker_name), shell=True).decode().split(' \r\n')[-2].split(' ')[0]
        except:
            pass

        return result

def print_usage(argv0):
    print("[*] Usage")
    print("sudo %s [-e, -c, -s] [brand] [firmwre_name]" % argv0)
    return

def runner(args):
    (idx, dh, mode, brand, firmware) = args
    if os.path.isfile(firmware):
        docker_name = dh.run_core(idx, mode, brand, firmware)
        dh.stop_core(docker_name)
    else:
        logging.error("[-] Can't find firmware file")

def main():
    if len(sys.argv) < 2:
        print_usage(sys.argv[0])
        exit(1)

    firmae_root=os.path.abspath('.')
    dh = docker_helper(firmae_root, remove_image=False)

    if sys.argv[1] in ['-ec', '-ea']:
        if len(sys.argv) < 4:
            print_usage(sys.argv[0])
            exit(1)

        if not os.path.exists(os.path.join(firmae_root, "scratch")):
            os.mkdir(os.path.join(firmae_root, "scratch"))

        brand = sys.argv[2]
        mode = '-' + sys.argv[1][-1]
        firmware_path = os.path.abspath(sys.argv[3])
        if os.path.isfile(firmware_path) and not firmware_path.endswith('.list'):
            argv = (0, dh, mode, brand, firmware_path)
            runner(argv)

        elif os.path.isfile(firmware_path) and firmware_path.endswith('.list') \
            or os.path.isdir(firmware_path):
            # TODO: check number of firmwares

            if os.path.isdir(firmware_path):
                firmwares = []
                for directory, sub_directory, filename_list in os.walk(firmware_path):
                    for filename in filename_list:
                        firmwares.append(os.path.join(directory, filename))

            else:
                # this accepts firmware list file
                with open(firmware_path, 'r') as f:
                    firmwares = f.read().splitlines()

            num_cores = mp.cpu_count()
            if len(firmwares) < num_cores:
                num_cores = len(firmwares)

            logging.info("[*] Using %d cores ..." % (num_cores))
            t0 = time.time()

            p = mp.Pool(num_cores)
            for idx, firmware in enumerate(firmwares):
                arg=(idx, dh, mode, brand, firmware)
                p.apply_async(runner, args=(arg,))
                time.sleep(1)
            p.close()
            p.join()

            logging.info("[*] Processing %d firmware done. (%0.4fs)",
                         len(firmwares), time.time() - t0)

    elif sys.argv[1] in ['-er', '-ed']:
        if len(sys.argv) < 3:
            print_usage(sys.argv[0])
            exit(1)

        mode = '-' + sys.argv[1][-1]
        firmware_path = os.path.abspath(sys.argv[2])
        if os.path.isfile(firmware_path):
            argv = (0, dh, mode, "auto", firmware_path)
            runner(argv)

    elif sys.argv[1] == '-c':
        if len(sys.argv) != 3:
            print_usage(sys.argv[0])
            exit(1)

        cmd = sys.argv[2]
        for core in dh.get_container_list():
            print(core)
            print(dh.run_command(core, cmd))

    elif sys.argv[1] == '-s':
        if len(sys.argv) != 3:
            print_usage(sys.argv[0])
            exit(1)

        script = sys.argv[2]
        for core in dh.get_container_list():
            print(core)
            print(dh.run_script(core, script))

if __name__ == "__main__":
    main()
