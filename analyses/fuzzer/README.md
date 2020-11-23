This directory contains analyses for the FirmAE system.

* `fuzzer.py`: This is a main script for testing command injection and buffer overflow vulnerability.
* `hnap_pair`: Default key-value pair information for a HNAP request.
* `login.py`: This script helps to login the webpages on the emulated firmware.

Fuzzer works with two steps to find command injection and one step for buffer overflow.
 1. Parse parameters in xml, php, html pages for the web pages in target system filesystem.
 2. Command injection
   - Spray signatures such as `d34d1`, `d34d2`, ...
   - Find signatures with a execve system call in the kernel log of target emulation.
   - Send vulnerable command injection combination for the found vulnerable parameters on web page.
3. Buffer overflow
   - Spray large buffer with a signature such as `aaaaaaa1...aaaaaaa1`, ..., `aaaaaa10...aaaaaa10`, ...

Found vulnerability
* Command injection in a Belkin product reported through bugcrowd
* CVE-2018-19986
* CVE-2018-19987
* CVE-2018-19988
* CVE-2018-19989
* CVE-2018-19990
* CVE-2018-20114 D-Link soap.cgi command injection
* CVE-2019-11399 TRENDNet command injection
* CVE-2019-11400 TRENDNet buffer overflow
* CVE-2019-6258 D-Link buffer overflow
* CVE-2019-20082 ASUS buffer overflow
* CVE-2019-20084 