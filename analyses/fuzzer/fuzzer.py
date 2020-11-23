#!/usr/bin/env python3

from xml.etree.ElementTree import parse
from bs4 import BeautifulSoup
import sys
import subprocess
import socket
import time
import datetime
import re
import login
import requests

MODE = None
BRAND = None
IID = None
TARGET = None
LOGIN_TYPE = 'unknown'
SESSION = None
UNIQ = '| sort | uniq'
AWK_UNIQ = '| awk \'{split($0,a,":"); print a[1]}\'' + UNIQ
CUT_CGI = " | sed 's@\\(\\.cgi\\).*@\\1@' | sed 's@.*\\(/\\)@\\1@' | sed 's@.*\\( \\)@\\1@' | sed 's@.*\\(\"\\)@\\1@'"
GREP_CGI = " | grep -P '^/?[A-Za-z0-9]+\.cgi$'"
GREP_PARAM = " | grep -P '^(\?)?[A-Za-z0-9]+=$'"
GREP_HEADER = " | grep -P '^(\?)?[A-Za-z0-9]+:$'"
GREP_HNAP = " | grep -P '/HNAP1/[A-Za-z0-9]+'"
CUT_PARAM = " | sed 's@[a-z]*\\(\\=\\).*@\\1@' | sed 's@.*\\(?\\)@\\1@'"
UPNP_REGEX = '[A-Za-z0-9-]+:[A-Za-z0-9:-]*'
HNAP_REGEX = '/HNAP1/[A-Za-z0-9]+'

PAYLOAD_LIST = []
key_value_map = {}

POST_PACKET = '''POST {uri} HTTP/1.1
Host: {host}
Content-Type: text/xml
Content-Length: {length}
{header}
{body}'''

HNAP_PACKET = '''POST /HNAP1/ HTTP/1.1
Host: {host}
SOAPAction: "http://purenetworks.com{soap}"
Content-Length: {length}
{header}
{data}'''

SOAP_PACKET = '''POST {uri}?{param}{payload} HTTP/1.1
Host: {host}
Content-Type: text/xml
SOAPAction: "whatever-serviceType#whatever-action"
Content-Length: {length}
{header}
{body}'''

# ST:urn:schemas-upnp-org:service:WANIPConnection:1;{};ls\r\n".format(cmd)
# ST:uuid:`" + cmd + b"`
SSDP_PACKET = '''M-SEARCH * HTTP/1.1
Host:239.255.255.250:1900
ST:{st}
MX:2
Man:"ssdp:discover"

'''

makebuf = lambda n : ('a'*(8-len(str(n)))+ str(n))*1250

def readHTML(filepath):
    with open(filepath, 'rb') as f:
        data = re.sub(b"(<!--.*?-->)", b"", f.read(), flags=re.MULTILINE)
        return data.decode()
    return ''

def command(cmd):
    try:
        result = subprocess.check_output(cmd, shell=True)
        result = result.decode().split('\n')[:-1]
    except:
        result = ''

    return result

def preprocess():
    for q_l in ['', '\'', '"']:
        for q_r in ['', '\'', '"', '#']:
            for sep in ['&&', '|', '||',  ';', '`']:
                PAYLOAD_LIST.append(q_l + sep + 'a' + sep + q_r)

def get_open_port():
    results = []
    tmp_port_map = {'1900':False, '5000':False}
    tree = parse('./analyses_log/{}/{}/nmap_log.txt'.format(BRAND, IID))
    nmap = tree.getroot()
    for host in nmap.iter('host'):
        for ports in host.iter('ports'):
            for port, state in zip(ports.iter('port'), ports.iter('state')):
                port_num = port.attrib.get('portid')
                if port_num in tmp_port_map:
                    tmp_port_map[port_num] = True
                results.append({'port': port_num, 'state': state.attrib.get('state'), 'files':[], 'uris':[], 'params':[], 'headers':[]})

    for port in tmp_port_map:
        if not tmp_port_map[port]:
            results.append({'port': port, 'state': 'unknown', 'files':[], 'uris':[], 'params':[], 'headers':[]})

    return results

def extract_image():
    command('mkdir {} 2> /dev/null'.format(IID))
    command('tar xzf ../images/{}.tar.gz -C ./{} 2> /dev/null'.format(IID, IID))

def get_information():
    # cgibin, fileaccess.cgi in DIR-816L_REVB_FIRMWARE_PATCH_2.06.B09_BETA.ZIP
    cgi_map = {'uri':[], 'param':[], 'header':[]}
    action_map = {}
    hnap_map = {}
    binary_list = []
    param_map = {}
    ssdp_list = []

    for filepath in command('find ./{} -executable -iname "*cgi*"'.format(IID)):
        binary_list.append(filepath)
        for cgi in command('strings {} {} {}'.format(filepath, GREP_CGI, UNIQ)):
            if cgi[0] != '/':
                cgi = '/' + cgi
            if cgi != '' and cgi not in cgi_map['uri']:
                cgi_map['uri'].append(cgi)
        for param in command('strings {} {} {}'.format(filepath, GREP_PARAM, UNIQ)):
            if param[0] == '?':
                param = param[1:]
            if param != '' and param not in cgi_map['param']:
                cgi_map['param'].append(param)

        for header in command('strings {} {} {}'.format(filepath, GREP_HEADER, UNIQ)):
            if header != '' and header not in cgi_map['header']:
                cgi_map['header'].append(header)

    # /htdocs/upnp/ssdpcgi -> /htdocs/cgibin in DIR-816L_REVB_FIRMWARE_PATCH_2.06.B09_BETA.ZIP
    for filepath in command('find ./{} -iname "*.cgi"'.format(IID)):
        uri = filepath[filepath.rfind('/'):]
        if uri != '' and uri not in cgi_map['uri']:
            cgi_map['uri'].append(uri)

    # get hnap information
    for line in command("egrep -r 'soap:Envelope' ./{} | grep -P 'hnap/[A-Za-z0-9]+.xml'".format(IID)):
        filepath = line[:line.find(':')]
        hnap = "/HNAP1/" + filepath.split('/')[-1][:-4]
        if hnap in hnap_map:
            continue
        with open(filepath, 'rb') as f:
            data = f.read()
            # dlink UTF8 data
            if data[:3] == b'\xef\xbb\xbf':
                data = data[3:].decode()
            else:
                data = data.decode()
            hnap_map[hnap] = data

    for filename in command('find ./{} -name "*upnp*"'.format(IID)):
        for line in command("strings {} | grep -P '{}'".format(filename, UPNP_REGEX)):
            for item in re.findall(UPNP_REGEX, line):
                if item not in ssdp_list:
                    ssdp_list.append(item)

    # TODO: more specify the grep
    for filepath in command('egrep -ril "action=" ./{}'.format(IID)):
        if filepath.find('.htm') != -1:
            try:
                soup = BeautifulSoup(readHTML(filepath), 'html.parser')
            except:
                continue
        # .asp, .aspx (dlink, netgear)
        elif filepath.find('.asp') != -1:
            response, status_code = send_http_dummy(port=80, uri='/' + filepath.split('/')[-1], method='get', need_login=True)
            if status_code == 200:
                response = re.sub(b"(<!--.*?-->)", b"", response, flags=re.MULTILINE)
                soup = BeautifulSoup(response.decode(), 'html.parser')
            else:
                continue
        else:
            continue

        for form_tag in soup.find_all('form'):
            action = form_tag.get('action')
            method = form_tag.get('method', 'get').lower()
            if action in ['/', '', None]:
                continue
            if action[0] != '/':
                action = '/' + action
            param_map = {}
            for input_tag in form_tag.find_all('input'):
                t = input_tag.get('type')
                if t in ['button', 'reset']:
                    continue
                name = input_tag.get('name')
                if not name:
                    if t == 'submit':
                        continue
                    name = input_tag.get('id')
                value = input_tag.get('value', 'default')
                #value = input_tag.get('value', '')
                if not value or value.find('(') != -1: # maybe function
                #if value and value.find('(') != -1: # maybe function
                    value = 'default'
                # linksys patch
                if BRAND == 'linksys':
                    if name == 'submit_button' and value in ['default', '']:
                        value = filepath.split('/')[-1].split('.')[0]
                    if name == 'action' and value == 'defualt':
                        value = 'Apply'
                value = value.encode('ascii', 'ignore').decode('ascii')
                if value:
                    param_map[name] = value

            if param_map:
                if not action_map.get(action):
                    action_map[action] = []
                for m, p in action_map[action]:
                    if p.get('html_response_return_page', 'false') == param_map.get('html_response_return_page'):
                        break
                else:
                    action_map[action].append([method, param_map])

    # HNAP key value
    for filepath in command('egrep -ril "result_xml.Set" ./{}'.format(IID)):
        scripts = []
        if filepath.find('.htm') != -1:
            try:
                soup = BeautifulSoup(readHTML(filepath), 'html.parser')
                for script in soup.find_all('script', type='text/javascript'):
                    scripts.append(script.text)
            except:
                continue
        elif filepath.find('.js') != -1:
            scripts.append(readHTML(filepath))
        else:
            continue

        regex = re.compile("result_xml.Set\(.*,.*\);")
        for script in scripts:
            for function_line in regex.findall(script):
                key, value = function_line[15:-2].split(',')
                key = key.strip()
                value = value.strip()
                key = key[key.rfind('/') + 1 : -1]
                if value[0] != '"' or value[1] == '"':
                    continue
                value = value[1:-1]
                if key not in key_value_map:
                    if value == 'false':
                        value = 'true'
                    elif value == 'Disable':
                        value = 'Enable'
                    elif value == 'DENY':
                        value = 'ALLOW'
                    key_value_map[key] = value

    print('[*] cgi_map')
    print(cgi_map)

    print('[*] hnap_map')
    for i in hnap_map:
        print(i)
        print(hnap_map[i])

    print('[*] ssdp_list')
    print(ssdp_list)

    print('[*] action_map')
    for i in action_map:
        print(i, action_map[i])

    print('[*] binary_list')
    print(binary_list)

    print('[*] key_value_map')
    print(key_value_map)

    return cgi_map, hnap_map, ssdp_list, action_map

def get_key_value(key):
    # well-known hardcoded-value
    if key == "CAPTCHA":
        return "false"
    elif key.find("Mac") != -1:
        return "11:22:33:44:55:66"
    elif key.find("IPv6Address") != -1:
        return "2001::1"
    # not mac address or IPv6 address
    elif key.endswith("Address") or key.endswith("IP"):
        return TARGET
    # dlink HNAP default password
    elif key == "AdminPassword":
        return "admin"
    # make login fail
    elif key == "ChangePassword":
        return "false"
    elif key in key_value_map:
        return key_value_map[key]
    else:
        return 'default'

def clear_image():
    command('rm -rf ./{} 2> /dev/null'.format(IID))

def get_execve_log(dummy_length):
    execve_list = []
    for line in command('strings ../scratch/{}/qemu.final.serial.log | grep "\[ANALYZE\]" | grep -i d34d'.format(IID)):
        match = re.search('d34d[0-9]+', line, re.IGNORECASE).group()

        num = int(match[4:])
        while num > dummy_length:
            num = num // 10

        if num not in execve_list:
            execve_list.append(num)

    return execve_list

def send_packet(port, packet):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((TARGET, port))
        sock.send(packet.encode())
        data = sock.recv(1024 * 1024)
        sock.close()
        time.sleep(0.01)
        return data
    except:
        return b''

def send_udp_packet(port, packet):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(packet.encode(), (TARGET, port))
    time.sleep(0.1) # because it doesn't return

def send_soap_dummy(port, uri, param, payload, header):
    host = TARGET + ':' + str(port)
    post_data = param + payload
    packet = SOAP_PACKET.format(uri = uri, param = param, payload = payload, host = host, length = str(len(post_data)), body = post_data, header = header)
    send_packet(port, packet)

def send_hnap_dummy(port, hnap, data='', header='', need_login=False):
    headers = requests.utils.default_headers()
    headers["Origin"] = "http://" + TARGET
    headers["SOAPACTION"] = '"http://purenetworks.com{}"'.format(hnap)
    headers["Accept"] = "text/xml"
    headers["Referer"] = "http://" + TARGET + "/info/Login.html"
    cookies = {}
    req = requests
    if need_login:
        global LOGIN_TYPE, SESSION
        if not SESSION:
            LOGIN_TYPE, SESSION = login.get_session(BRAND, TARGET)
        if LOGIN_TYPE == 'dlink_hnap':
            cookies = SESSION
            headers["HNAP_AUTH"] = login.HNAP_AUTH(hnap.split('/')[-1], login.PRIVATE_KEY)
        else:
            req = SESSION
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36"

    headers["Content-Type"] = "text/xml; charset=UTF-8"
    headers["X-Requested-With"] = "XMLHttpRequest"

    try:
        r = req.post('http://{}:{}/HNAP1/'.format(TARGET, port), headers=headers, data=data.encode(), cookies=cookies, timeout=10.0)
        data = r.text.encode()
        if data[9:12] == b'401':
            return data, 401
        else:
            return data, r.status_code
    except:
        return b'', 503

def send_ssdp_dummy(port, st):
    packet = SSDP_PACKET.format(st=st)
    send_udp_packet(port, packet)

def send_http_dummy(port, uri, method, headers={}, params={}, need_login=False):
    global SESSION, LOGIN_TYPE
    headers['Content-Type'] = 'text/xml'
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko'
    req = requests
    if need_login:
        if not SESSION:
            LOGIN_TYPE, SESSION = login.get_session(BRAND, TARGET)
        req = SESSION
    headers['Referer'] = 'http://{}/'.format(TARGET)
    try:
        if method == 'get':
            r = req.get('http://{}:{}{}'.format(TARGET, port, uri), headers=headers, params=params, timeout=10.0)
        elif method == 'post':
            r = req.post('http://{}:{}{}'.format(TARGET, port, uri), headers=headers, data=params, timeout=10.0)
        else:
            return b'', 503
    except:
        return b'', 503

    data = r.text.encode()

    # leave this field blank = leave blank on belkin
    # user_page.asp on dlink
    # login.htm, login.ccp for trendnet
    if data.find(b'leave this field blank') != -1 or data.find(b'user_page.asp') != -1 or data.find(b'location.replace(\'login.htm\')') != -1 or data.find(b'login.ccp') != -1:
        if need_login == True and LOGIN_TYPE != 'unknown':
            SESSION = None
            return send_http_dummy(port, uri, method, headers, params, True)
        else:
            return data, 401
    else:
        return data, r.status_code

def get_hnap_reqs(template, idx):
    length = len(re.findall('></', template))
    data_list = ['' for i in range(length)]
    template_list = template.split('></')
    PREFIX = ''

    for cur_idx, string in enumerate(template_list[:-1]):
        for tmp_idx in range(length):
            if cur_idx == tmp_idx:
                if MODE == 'bof':
                    data_list[tmp_idx] += PREFIX + string + '>' + makebuf(idx)
                elif MODE == 'ci':
                    data_list[tmp_idx] += PREFIX + string + '>d34d' + str(idx)
            else:
                key = string[string.rfind('<') + 1:]
                data_list[tmp_idx] += PREFIX + string + '>' + get_key_value(key)
        idx += 1
        PREFIX = '</'

    for i in range(length):
        data_list[i] += PREFIX + template_list[-1]

    return data_list

def fuzz(dummy_info):
    # TODO: resend when fail
    if dummy_info[0] == 'soap_param':
        for payload in PAYLOAD_LIST:
            send_soap_dummy(dummy_info[1], dummy_info[2], dummy_info[3], payload, '')
            time.sleep(1)
    elif dummy_info[0] == 'soap_header':
        for payload in PAYLOAD_LIST:
            send_soap_dummy(dummy_info[1], dummy_info[2], '', '', '{} {}\n'.format(dummy_info[3], payload))
            time.sleep(1)
    elif dummy_info[0] == 'hnap_header':
        for payload in PAYLOAD_LIST:
            send_hnap_dummy(port=dummy_info[1], hnap=dummy_info[2] + '/' + payload)
    elif dummy_info[0] == 'hnap_data':
        for payload in PAYLOAD_LIST:
            response, status_code = send_hnap_dummy(port=dummy_info[1], hnap=dummy_info[2], data=dummy_info[3].format(payload=payload), need_login=dummy_info[4])
            if response.find(b'>OK<') == -1 and response.find(b'>SUCCESS<') == -1 and response.find(b'>REBOOT<') == -1:
                time.sleep(10)
                continue
            print('[+] ok')
            print(dummy_info[3].format(payload=payload))
            time.sleep(10)
    elif dummy_info[0] == 'ssdp':
        for payload in PAYLOAD_LIST:
            send_ssdp_dummy(dummy_info[1], dummy_info[2] + payload)
    elif dummy_info[0] == 'cookie':
        for payload in PAYLOAD_LIST:
            send_http_dummy(port = dummy_info[1], method = 'get', uri = '/', headers = {'Cookie':dummy_info[2] + payload})
    elif dummy_info[0] == 'action':
        for payload in PAYLOAD_LIST:
            dummy_info[4][dummy_info[5]] = payload
            response, status_code = send_http_dummy(port = dummy_info[1], method = dummy_info[2], uri = dummy_info[3], params = dummy_info[4], need_login = dummy_info[6])
            if status_code == 401:
                response, status_code = send_http_dummy(port = dummy_info[1], method = dummy_info[2], uri = dummy_info[3], params = dummy_info[4], need_login = True)
            print('[+] ok')
            print(response)
            time.sleep(5)
    else:
        print('unknown dummy info')

def send_dummy(infos, cgi_map, hnap_map, ssdp_list, action_map):
    dummy_idx_list = []
    idx = 0
    for info in infos:
        print('[*] test ' + info['port'])
        port = int(info['port'])
        if port in [80, 8181, 8080]:
            for hnap in hnap_map:
                # SetUSBStorageSettings crash in DIR822B1_FW202KRb06
                if hnap in ['/HNAP1/Reboot', '/HNAP1/SetInternetProfileAlpha', '/HNAP1/SetUSBStorageSettings']:
                    continue

                # dlink hnap CVE-2015-2051
                send_hnap_dummy(port=port, hnap=hnap + '/d34d' + str(idx))
                dummy_idx_list.append(['hnap_header', port, hnap])
                idx += 1

                # send hnap data signature
                data_list = get_hnap_reqs(hnap_map[hnap], idx)
                for data in data_list:
                    response, status_code = send_hnap_dummy(port=port, hnap=hnap, data=data)
                    print('[*] send {} signature without login {}'.format(hnap, datetime.datetime.now()))
                    need_login = status_code == 401
                    if need_login:
                        response, status_code = send_hnap_dummy(port=port, hnap=hnap, data=data, need_login=True)
                        print('[*] send {} signature with login {}'.format(hnap, datetime.datetime.now()))

                        if response.find(b'>OK<') != -1 or response.find(b'>SUCCESS<') != -1 or response.find(b'>REBOOT<') != -1:
                            time.sleep(9)
                        else: # login failed clear the session
                            global SESSION
                            SESSION = None
                    elif status_code == 200:
                        print('[+] info leak {} with no authentication'.format(hnap))
                    else:
                        print('[-] response error {}'.format(hnap))

                    time.sleep(1)
                    print(data)
                    print(response)

                    # for the payload test
                    dummy_idx_list.append(['hnap_data', port, hnap, data.replace('d34d' + str(idx), '{payload}'), need_login])
                    idx += 1

            for uri in action_map:
                # trendnet TEW-651BR_2.x_, TEW-652BRP_3.04B01, TEW-652BRU_1.00b12 login
                if uri in ['/login.ccp', 'fwupgrade.ccp']:
                    continue

                for method, params in action_map[uri]:
                    # changed account info in get_set.ccp, login.htm
                    # unknown crash in time.htm trendnet
                    if params.get('nextPage', 'default') in ['login.htm', 'time.htm']:
                        continue
                    for key in params:
                        need_login = False
                        original = params[key]
                        if MODE == 'bof':
                            params[key] = makebuf(idx)
                        elif MODE == 'ci':
                            params[key] = 'd34d' + str(idx)
                        response, status_code = send_http_dummy(port=port, method=method, uri=uri, params=params)

                        need_login = status_code == 401
                        if need_login:
                            response, status_code = send_http_dummy(port=port, method=method, uri=uri, params=params, need_login=True)

                            print('[*] send {} signature {}'.format(uri, datetime.datetime.now()))
                            time.sleep(9)
                        elif status_code == 200:
                            print('[+] info leak {} with no authentication'.format(uri))
                        else:
                            print('[-] response error {}'.format(uri))

                        print(params)
                        print(response)
                        time.sleep(1)
                        dummy_idx_list.append(['action', port, method, uri, params, key, need_login])
                        params[key] = original
                        idx += 1

            # cookie command injection
            send_http_dummy(port=port, method='get', uri='/', headers={'Cookie': 'i:d34d' + str(idx)})
            dummy_idx_list.append(['cookie', port, 'i:'])
            idx += 1

        #if info['port'] == '49152': # dlink soap.cgi CVE2018-6530
        if port not in [23, 22, 53, 443, 1900, 5000]:
            for uri in cgi_map['uri']:
                for param in cgi_map['param']:
                    if MODE == 'bof':
                        send_soap_dummy(port, uri, param, makebuf(idx), '')
                    elif MODE == 'ci':
                        send_soap_dummy(port, uri, param, 'd34d' + str(idx), '')
                    dummy_idx_list.append(['soap_param', port, uri, param])
                    idx += 1
                    print('[*] send {} param signature {}'.format(uri, idx))
                    print(param)
                    time.sleep(1)

                for header in cgi_map['header']:
                    if MODE == 'bof':
                        send_soap_dummy(port, uri, '', '', '{} {}\n'.format(header, makebuf(idx)))
                    elif MODE == 'ci':
                        send_soap_dummy(port, uri, '', '', '{} d34d{}\n'.format(header, idx))
                    dummy_idx_list.append(['soap_header', port, uri, header])
                    idx += 1
                    print('[*] send {} header signature {}'.format(uri, idx))
                    print(header)
                    time.sleep(1)

        # dir_300_645_815_upnp_rce
        # 1900 for dlink, 5000 for netgear
        if port in [1900, 5000]:
            for ssdp in ssdp_list:
                if MODE == 'bof':
                    send_ssdp_dummy(port, ssdp + makebuf(idx))
                elif MODE == 'ci':
                    send_ssdp_dummy(port, ssdp + 'd34d' + str(idx))
                dummy_idx_list.append(['ssdp', port, ssdp])
                idx += 1
            time.sleep(1)

    return dummy_idx_list

def main():
    preprocess()
    infos = get_open_port()
    print("[*] ports info")
    print(infos)

    if infos:
        extract_image()
        cgi_map, hnap_map, ssdp_list, action_map = get_information()
        clear_image()

        dummy_list = send_dummy(infos, cgi_map, hnap_map, ssdp_list, action_map)
        time.sleep(10)

        dummy_idx_list = get_execve_log(len(dummy_list))

        for idx in dummy_idx_list:
            print('[+] {}'.format(dummy_list[idx]))
            fuzz(dummy_list[idx])

if __name__ == "__main__":
    argc = len(sys.argv)
    if argc != 5:
        print("usage: fuzzer.py [mode] [brand] [iid] [target]")
        exit()

    MODE = sys.argv[1]
    BRAND = sys.argv[2]
    IID = sys.argv[3]
    TARGET = sys.argv[4]

    main()
