#coding:utf-8
'''
Created on 2016年10月2日
@author: 肖雄
'''
from weixin import *
import subprocess
import requests


class WXLogin(WebWeixin):
    
    def __init__(self):
        '''添加图形选项，如果-NG运行xdg-open生成二维码，否则命令行输出二维码'''
        super(WXLogin, self).__init__()
        self.graph = 'true'
        self.q = multiprocessing.Queue()
       
    def _post(self, url, params, jsonfmt=True):
            if jsonfmt:
                request = urllib2.Request(url=url, data=json.dumps(params))
                request.add_header(
                    'ContentType', 'application/json; charset=UTF-8')
            else:
                request = urllib2.Request(url=url, data=urllib.urlencode(params))
            response = urllib2.urlopen(request)
            data = response.read()
            data = data.decode('utf-8')
            if jsonfmt:
                return json.loads(data)
            return data

    
    def genQRCode(self):
        '''生成二维码，添加在linux平台下调用xdg打开二维码'''
        url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
        params = {
            't': 'webwx',
            '_': int(time.time()),
        }
        request = urllib2.Request(url=url, data=urllib.urlencode(params))
        response = urllib2.urlopen(request)
        data = response.read()
        QRCODE_PATH = self._saveFile('qrcode.jpg', data, '_showQRCodeImg')
        print sys.platform
        print self.graph
        if sys.platform.startswith('win'):
            subprocess.call(['open',QRCODE_PATH])
        elif sys.platform.find('linux')>= 0 and self.graph:
            subprocess.call(['xdg-open', QRCODE_PATH])
        else :
            self._str2qr('https://login.weixin.qq.com/qrcode/' + self.uuid)
            
    def login_module(self):
        self._echo(u'[*] 微信网页版 ... 登陆')
        while True:
            self._run(u'[*] 正在获取 uuid ... ', self.getUUID)
            self._echo(u'[*] 正在获取二维码 ... 成功')
            self.genQRCode()
            self._echo(u'[*]正在生成二维码...成功')
            print '[*] 请使用微信扫描二维码以登录 ... '
            if not self.waitForLogin():
                continue
                print u'[*] 请在手机上点击确认以登录 ... '
            if not self.waitForLogin(0):
                continue
            break

        self._run(u'[*] 正在登录 ... ', self.login)
        self._run(u'[*] 微信初始化 ... ', self.webwxinit)
        self._run(u'[*] 开启状态通知 ... ', self.webwxstatusnotify)
        self._run(u'[*] 获取联系人 ... ', self.webwxgetcontact)
        self._echo(u'[*] 应有 %s 个联系人，读取到联系人 %d 个' %
                   (self.MemberCount, len(self.MemberList)))
        self._echo(u'[*] 共有 %d 个群 | %d 个直接联系人 | %d 个特殊账号 ｜ %d 公众号或服务号' % (len(self.GroupList),
                                                                         len(self.ContactList), len(self.SpecialUsersList), len(self.PublicUsersList)))
     
        
    @catchKeyboardInterrupt
    def start(self):
        self._echo(u'[*] 微信网页版 ... 开动')
        print
        logging.debug(u'[*] 微信网页版 ... 开动')
        while True:
            self._run(u'[*] 正在获取 uuid ... ', self.getUUID)
            self._echo(u'[*] 正在获取二维码 ... 成功')
            print
            logging.debug(u'[*] 微信网页版 ... 开动')
            self.genQRCode()
            print '[*] 请使用微信扫描二维码以登录 ... '
            if not self.waitForLogin():
                continue
                print u'[*] 请在手机上点击确认以登录 ... '
            if not self.waitForLogin(0):
                continue
            break

        self._run(u'[*] 正在登录 ... ', self.login)
        self._run(u'[*] 微信初始化 ... ', self.webwxinit)
        self._run(u'[*] 开启状态通知 ... ', self.webwxstatusnotify)
        self._run(u'[*] 获取联系人 ... ', self.webwxgetcontact)
        self._echo(u'[*] 应有 %s 个联系人，读取到联系人 %d 个' %
                   (self.MemberCount, len(self.MemberList)))
        print
        self._echo(u'[*] 共有 %d 个群 | %d 个直接联系人 | %d 个特殊账号 ｜ %d 公众号或服务号' % (len(self.GroupList),
                                                                         len(self.ContactList), len(self.SpecialUsersList), len(self.PublicUsersList)))
        print
        self._run(u'[*] 获取群 ... ', self.webwxbatchgetcontact)
        logging.debug(u'[*] 微信网页版 ... 开动')
        if self.DEBUG:
            print self
        logging.debug(self)

        if self.interactive and raw_input(u'[*] 是否开启自动回复模式(y/n): ') == 'y':
            self.autoReplyMode = True
            print u'[*] 自动回复模式 ... 开启'
            logging.debug(u'[*] 自动回复模式 ... 开启')
        else:
            print u'[*] 自动回复模式 ... 关闭'
            logging.debug(u'[*] 自动回复模式 ... 关闭')

        listenProcess = multiprocessing.Process(target=self.listenMsgMode)
        listenProcess.start()

        while True:
            text = raw_input('')
            text = text.decode(sys.stdin.encoding)
            logging.info(text.encode('utf-8'))
            if text == 'quit':
                listenProcess.terminate()
                print(u'[*] 退出微信')
                logging.debug(u'[*] 退出微信')
                exit()
            elif text[:2] == '->':
                [name, word] = text[2:].split(':')
                logging.info((name + ':name,' + word + 'word').encode('utf-8'))
                if name == 'all':
                    self.sendMsgToAll(word)
                else:
                    self.sendMsg(name, word)
            elif text[:3] == 'm->':
                [name, file] = text[3:].split(':')
                self.sendMsg(name, file, True)
            
    
    def handleMsg(self, r):
        
        for msg in r['AddMsgList']:
            
            msgType = msg['MsgType']
            name = self.getUserRemarkName(msg['FromUserName'])
            content = msg['Content']
            msgid = msg['MsgId']


            if msgType == 1:
                print u'你有新的文本消息'
                self.q.put(r)
                print 'qsize' + str(self.q.qsize())
    
                raw_msg = {'raw_msg': msg}
                self._showMsg(raw_msg)
                if self.autoReplyMode:
                    ans = self._xiaodoubi(content) + '\n[微信机器人自动回复]'
                    if self.webwxsendmsg(ans, msg['FromUserName']):
                        print '自动回复: ' + ans
                        logging.info('自动回复: ' + ans)
                    else:
                        print '自动回复失败'
                        logging.info('自动回复失败')
                
                if content[0:4] == u'cmd:':
                    cmd = content[4:]
                    res = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
                    self.sendMsg(name, 'stdout:' + res.stdout.read() + '    stderr:' + res.stderr.read())
                    
                    stdout, stderr = res.communicate()
                    res.wait()
                    print u'子进程已经关闭'
    
            
            elif msgType == 10002:
                raw_msg = {'raw_msg': msg, 'message': u'%s 撤回了一条消息' % name}
                self._showMsg(raw_msg)
            else:
                raw_msg = {
                    'raw_msg': msg, 'message': u'[*] 该消息类型为: %d，可能是表情，图片, 链接或红包' % msg['MsgType']}
                #self._showMsg(raw_msg)
                
                
if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    import coloredlogs
    coloredlogs.install(level='INFO')

    webwx = WXLogin()
    webwx.start()
        
        
        
        
        
