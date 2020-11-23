#!/usr/bin/env python3

import sys
import re
import os
import selenium
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# typical netgear firmwares...
# "No, I want to configure the Internet connection myself."
# R6200v2
# "No. I want to manually enter configuration settings using the NETGEAR genie wizard."
netgear_pattern = re.compile(r"No[,.]( I want to).+(configur)")

def Initialize():
    os.environ['PATH'] = os.getcwd() + ':' + os.environ['PATH']

class Initializer:
    brand = None
    auth = None
    ip = None
    driver = None
    pattern = None

    def __init__(self, brand, ip):
        self.brand = brand
        self.ip = ip

        if self.brand == "netgear":
            self.auth = "admin:password"
            self.pattern = re.compile(r"No[,.]( I want to).+(configur)")
        elif self.brand == "asus":
            self.auth = "admin:admin"
            self.pattern = re.compile(r"(Quick Internet Setup)")
        elif self.brand == 'dlink':
            self.pattern = re.compile(r'<div id="wizard_title">Welcome</div>')

    def Connect(self):
        options = webdriver.ChromeOptions()
        options.binary_location = '/usr/bin/google-chrome-stable'
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--screen-size=1200x600')
        self.driver = webdriver.Chrome(chrome_options=options)
        if self.auth:
            self.driver.get('http://' + self.auth + '@' + self.ip)
        else:
            self.driver.get('http://' + self.ip)
        time.sleep(30)

    def Run(self):
        if self.SwitchFrame(self.pattern):
            print("[*] Find menu success!")
        else:
            print("[-] Couldn't find manual setting information")
            return

        if self.brand == "netgear":
            idx = self.GetRadioIdx(self.driver.page_source)
            self.ClickRadio(idx)
            self.ClickNext()
            time.sleep(10)
        elif self.brand == "asus":
            self.driver.execute_script("location.href = '/QIS_wizard.htm?flag=wireless';")
            time.sleep(10)
            self.SwitchFrame(re.compile("smartcon_skip"))
            self.driver.execute_script("return smartcon_skip();")
            time.sleep(10)
        elif self.brand == "dlink":
            # COVR-3902_REVA_ROUTER_FIRMWARE_v1.01B05
            self.driver.execute_script("clearCreateRulePOP();")
            time.sleep(10)

    def GetAlert(self):
        try:
            alert = self.driver.switch_to_alert()
            return alert
        except:
            return None

    def Close(self):
        alert = self.GetAlert()
        if alert: # authentication alert
            alert.dismiss()
        self.driver.close()

    def SwitchFrame(self, pattern):
        self.driver.switch_to_default_content()
        if pattern.search(self.driver.page_source):
            return True

        for frame_name in ['frame', 'iframe']:
            for frame in self.driver.find_elements_by_tag_name(frame_name):
                self.driver.switch_to_frame(frame)
                if pattern.search(self.driver.page_source):
                    return True
                self.driver.switch_to_default_content()

        return False

    def GetRadioIdx(self, page):
        return page.count('"radio"', 0, netgear_pattern.search(page).start()) - 1

    def ClickRadio(self, idx):
        self.driver.find_elements_by_xpath("//*[@type='radio']")[idx].click()

    def ClickNext(self):
        if self.driver.page_source.find('btnsContainer_div') != -1: # wnr2000v3, WNDR3800, JNR3210, R6200v2
            self.driver.find_element_by_id('btnsContainer_div').click()
        else: # WNR3500Lv2, WNDR3400v3, R8000
            self.driver.find_element_by_xpath("//*[@type='button']").click()
        alert = self.driver.switch_to_alert()
        alert.accept()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: %s [brand] [IP]" % sys.argv[0])
        exit(1)

    if sys.argv[1] not in ['netgear', 'asus', 'dlink']:
        exit(0)

    Initialize()

    initializer = Initializer(sys.argv[1], sys.argv[2])
    initializer.Connect()

    initializer.Run()
    initializer.Close()

    # some netgear firmware redirect to the public page at first time
    initializer.Connect()
    initializer.Close()
