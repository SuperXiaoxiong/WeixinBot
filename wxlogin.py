#coding:utf-8
'''
Created on 2016年10月2日
@author: 肖雄
'''
from weixin import *
import subprocess
import requests
import threading
import webbrowser

class WXLogin(WebWeixin):
    
    def __init__(self):
        '''添加图形选项，如果-NG运行xdg-open生成二维码，否则命令行输出二维码'''
        super(WXLogin, self).__init__()
        self.graph = 'true'
        self.q = multiprocessing.Queue()

        self.loggerRetcode = logging.getLogger('test_logger')        
        formatter = logging.Formatter('%(asctime)s %(filename)s %(name)s %(message)s ' )
        sh = logging.FileHandler('tmp.log',mode='a',encoding=sys.getfilesystemencoding())
        sh.setFormatter(formatter)
        sh.setLevel(logging.INFO)
        self.loggerRetcode.addHandler(sh)
        self.loggerRetcode.setLevel(logging.INFO)
       
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
            #subprocess.call(['open',QRCODE_PATH])
            webbrowser.open(QRCODE_PATH)
        elif sys.platform.find('linux')>= 0 and self.graph:
            subprocess.call(['xdg-open', QRCODE_PATH])
        else :
            self._str2qr('https://login.weixin.qq.com/qrcode/' + self.uuid)
    
    def shell_recv(self,th):
        while True:
            text = th.stdout.readline()
            self.webwxsendmsg(text.rstrip(), self.cmder)
    
    
    def webwxgetcontact(self):
        SpecialUsers = self.SpecialUsers
        print self.base_uri
        url = self.base_uri + '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
            self.pass_ticket, self.skey, int(time.time()))
        
        try:
            dic = self._post(url, {})
        except Exception,e:
            print str(e)
            self.loggerRetcode.warning(str(e))
            return self.webwxgetcontact()
        else:   
            self.MemberCount = dic['MemberCount']
            self.MemberList = dic['MemberList']
            ContactList = self.MemberList[:]
            GroupList = self.GroupList[:]
            PublicUsersList = self.PublicUsersList[:]
            SpecialUsersList = self.SpecialUsersList[:]
    
            for i in xrange(len(ContactList) - 1, -1, -1):
                Contact = ContactList[i]
                if Contact['VerifyFlag'] & 8 != 0:  # 公众号/服务号
                    ContactList.remove(Contact)
                    self.PublicUsersList.append(Contact)
                elif Contact['UserName'] in SpecialUsers:  # 特殊账号
                    ContactList.remove(Contact)
                    self.SpecialUsersList.append(Contact)
                elif Contact['UserName'].find('@@') != -1:  # 群聊
                    ContactList.remove(Contact)
                    self.GroupList.append(Contact)
                elif Contact['UserName'] == self.User['UserName']:  # 自己
                    ContactList.remove(Contact)
            self.ContactList = ContactList
    
            return True  
    
          
    def synccheck(self):
        params = {
            'r': int(time.time()),
            'sid': self.sid,
            'uin': self.uin,
            'skey': self.skey,
            'deviceid': self.deviceId,
            'synckey': self.synckey,
            '_': int(time.time()),
        }
        url = 'https://' + self.syncHost + \
            '/cgi-bin/mmwebwx-bin/synccheck?' + urllib.urlencode(params)
        
        try:
            #data = self._get(url)
            request = urllib2.Request(url=url)
            request.add_header(
                    'ContentType', 'application/json; charset=UTF-8')
            response = urllib2.urlopen(request, timeout=30)
            data = response.read()

        except urllib2.URLError, e:  
            print str(e)
            self.loggerRetcode.warning( str(e))
            print  ' urllib2.URLError  retcode : ' +'-1',  'selector: '   + '-1' , ' synchost : ' + self.syncHost
            self.loggerRetcode.warning( 'retcode : ' +'-1'+  'selector: '   + '-1' + ' synchost : ' + self.syncHost)
            return [-1, -1]
        except  Exception,e:
            print str(e)
            self.loggerRetcode.warning( str(e))
            print ' 222 retcode : ' +'-1',  'selector: '   + '-1' , ' synchost : ' + self.syncHost
            self.loggerRetcode.warning( 'retcode : ' +'-1' +  'selector: '   + '-1' +  ' synchost : ' + self.syncHost)
            return [-1, -1]
            
        pm = re.search(
                r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}', data)
        retcode = pm.group(1)
        selector = pm.group(2)
        self.loggerRetcode.info( 'retcode : ' +retcode +' selector: '   +  selector +  ' synchost : ' + self.syncHost)
        return [retcode, selector]
              
    def login_module(self):
        self._echo(u'[*] 微信网页版 ... 登陆')
        while True:
            self._run(u'[*] 正在获取 uuid ... ', self.getUUID)
            self._echo(u'[*] 正在获取二维码 ... 成功')
            self.genQRCode()
            self._echo(u'[*]正在生成二维码...成功')
            print u'[*] 请使用微信扫描二维码以登录 ... '
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
        #self.pipe = subprocess.Popen('/bin/sh',stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        #th = threading.Thread(target=self.shell_recv, args=(self.pipe,))
        #th.setDaemon(True)
        #th.start()
        
    def _xiaodoubi(self, word):
        url = 'http://www.tuling123.com/openapi/api'
        data = {
                'key':'848c537af170450480af8f519a2eed0c',
                'info':word
                }
        try:
            res = requests.post(url=url,data=json.dumps(data))
            res = json.loads(res.text)
            return res['text']
        except:
            return u"让我一个人静静 T_T..."   
        
        
    def reply_change(self,auto):
        self.autoReplyMode = auto
        if auto:
            print u'自动回复开启'
            self.loggerRetcode.info(u'自动回复开启')
        else:
            print u'自动回复关闭'
            self.loggerRetcode.info(u'自动回复关闭')
    
    
    def handleMsg(self, r):

        for msg in r['AddMsgList']:
            
            msgType = msg['MsgType']
            name = self.getUserRemarkName(msg['FromUserName'])
            content = msg['Content']
            msgid = msg['MsgId']


            if msgType == 1:
                self.q.put(r)
                print 'qsize' + str(self.q.qsize())
    
                raw_msg = {'raw_msg': msg}
                self._showMsg(raw_msg)
                

                        
                if content[0:4] == u'cmd:':
                    cmd = content[4:]
                    #self.pipe.stdin.write(cmd)
                    #self.pipe.stdin.flush()
                    #self.cmder = msg['FromUserName']
                
                elif  self.autoReplyMode:
                    ans = self._xiaodoubi(content) + u'\n[微信机器人自动回复]'
                    if self.webwxsendmsg(ans, msg['FromUserName']):
                        print u'自动回复: ' + ans
                    else:
                        print u'自动回复失败'
    
            
            elif msgType == 10002:
                raw_msg = {'raw_msg': msg, 'message': u'%s 撤回了一条消息' % name}
                self._showMsg(raw_msg)
            else:
                raw_msg = {
                    'raw_msg': msg, 'message': u'[*] 该消息类型为: %d，可能是表情，图片, 链接或红包' % msg['MsgType']}
                #self._showMsg(raw_msg)
                
