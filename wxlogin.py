#coding:utf-8
'''
Created on 2016年10月2日
@author: 肖雄
'''
from weixin import *
import subprocess
import requests
import threading
#import Queue

#class Timemessage(object):
  #  def __init__(self,fromname,toname,content,flagtime):
        
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
        #print data
        QRCODE_PATH = self._saveFile('qrcode.jpg', data, '_showQRCodeImg')
        print sys.platform
        print self.graph
        
        if sys.platform.startswith('win'):
            subprocess.call(['open',QRCODE_PATH])
        elif sys.platform.find('linux')>= 0 and self.graph:
            subprocess.call(['xdg-open', QRCODE_PATH])
        else :
            self._str2qr('https://login.weixin.qq.com/qrcode/' + self.uuid)
    
    def shell_recv(self,th):
        while True:
            text = th.stdout.readline()
            self.webwxsendmsg(text.rstrip(), self.cmder)
            
               
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
            return "让我一个人静静 T_T..."   
        
        
    def reply_change(self,auto):
        self.autoReplyMode = auto
        
    
    
    def handleMsg(self, r):
        for msg in r['AddMsgList']:
            #print msg
            srcName = None
            dstName = None
            groupName = None
            content = None
            sendtime = None
            flagtime = time.time()
            print flagtime
            srcName = self.getUserRemarkName(msg['FromUserName'])
            dstName = self.getUserRemarkName(msg['ToUserName'])
     
            sendtime = msg['CreateTime']
            
            msgType = msg['MsgType']
            content = msg['Content']
            msgid = msg['MsgId']
            if msg['FromUserName'][:2] == '@@':
                # 接收到来自群的消息
                if re.search(":<br/>", content, re.IGNORECASE):
                    [people, content] = content.split(':<br/>')
                    groupName = srcName
                    srcName = self.getUserRemarkName(people)
                    dstName = 'GROUP'
                else:
                    groupName = srcName
                    srcName = 'SYSTEM'
            elif msg['ToUserName'][:2] == '@@':
                # 自己发给群的消息
                groupName = dstName
                dstName = 'GROUP'
                
            if msgType == 1:
                self.q.put(r)
                print 'qsize' + str(self.q.qsize())
                raw_msg = {'raw_msg': msg}
                self._showMsg(raw_msg)
                if groupName != None:
                    if self.autoReplyMode:
                        ans = self._xiaodoubi(content) + u'\n[微信机器人自动回复]'
                        if self.webwxsendmsg(ans, msg['FromUserName']):
                            print u'自动回复: ' + ans
                        else:
                            print u'自动回复失败'
                            '''
                if content[0:4] == u'cmd:':
                    cmd = content[4:]
                    #self.pipe.stdin.write(cmd)
                    #self.pipe.stdin.flush()
                    #self.cmder = msg['FromUserName']
                    
                    '''
            elif msgType == 10002:
                raw_msg = {'raw_msg': msg, 'message': u'%s 撤回了一条消息' % srcName}
                self._showMsg(raw_msg)
            else:
                raw_msg = {
                    'raw_msg': msg, 'message': u'[*] 该消息类型为: %d，可能是表情，图片, 链接或红包' % msg['MsgType']}
                #self._showMsg(raw_msg)
                
