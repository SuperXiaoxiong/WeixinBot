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


def decode_list(data):
        rv = []
        for item in data:
            if isinstance(item, str):
                item = item.decode(sys.getfilesystemencoding())
            elif isinstance(item, list):
                item = decode_list(item)
            elif isinstance(item, dict):
                item = decode_dict(item)
            rv.append(item)
        return rv
    
def decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, str):
            key = key.decode(sys.getfilesystemencoding())
        if isinstance(value, str):
            value = value.decode(sys.getfilesystemencoding)
        elif isinstance(value, list):
            value = decode_list(value)
        elif isinstance(value, dict):
            value = decode_dict(value)
        rv[key] = value
    return rv
    

def encode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = encode_list(item)
        elif isinstance(item, dict):
            item = encode_dict(item)
        rv.append(item)
    return rv


def encode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = encode_list(value)
        elif isinstance(value, dict):
            value = encode_dict(value)
        rv[key] = value
    return rv


class timerJob(object):
    '''
    定时消息类，包括时间轴，收件人和发送的信息
    '''
    def __init__(self,priority,name,word):
        self.priority = priority
        self.name = name
        self.word = word
        return
    def __cmp__(self,other):
        return cmp(self.priority,other.priority)
    
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
        #print data
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
        #self.loggerRetcode.info( 'retcode : ' +retcode +' selector: '   +  selector +  ' synchost : ' + self.syncHost)
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
            #print msg
            srcName = None
            dstName = None
            groupName = None
            content = None
            sendtime = None
            #flagtime = time.time()
            #print flagtime
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
                #self.autoReplyMode = True
                if groupName == None:
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
    def sendAddfriend(self,toname):
        '''
        作用：发送好友添加请求
        参数：要添加的微信号
        返回值：成功或者失败
        '''
        pass
    def openGrouplist(self, groupname):
        '''
        作用：打开群列表
        参数：文件名
        返回值：群列表中用户列表
        '''
        gpath = './grouplist/'
        tmpplist = []
        try:
            tmpJsonFile = open(gpath + groupname,'r')
            tmpplist = json.load(tmpJsonFile)
        except BaseException,e:
            self.loggerRetcode(str(e))
            tmpplist = []
        finally:
            tmpJsonFile.close()
            return tmpplist
        
    def storeGrouplist(self, groupname, data):
        '''
        作用：保存群列表
        参数：文件名,数据
        '''
        gpath = './grouplist/'
        tmpJsonFile = open(gpath + groupname,'w')
        json.dump(data ,tmpJsonFile)
        tmpJsonFile.close()
                 
    def sendGroupmsg(self, groupname, word):
        '''
        作用：群发消息（以单人信息形式发送）
        参数：群名，发送内容
        '''
        gpath = './grouplist/'
        if os.path.isfile(gpath + groupname):
            grouplist = self.openGrouplist(groupname)
            for nameingroup in grouplist:
                print 'to ', nameingroup
                self.sendMsg(nameingroup, word)
        else:
            print u'群',groupname,u'不存在'
    
    def lsGroup(self):
        '''展示群列表'''
        groups = os.listdir('./grouplist')
        groups = decode_list(groups)
        print u'当前群列表为：(',len(groups),')'
        if len(groups) == 0:
            print u'暂无群发列表'
        else:
            for f in groups:
                print f
        return groups 
        '''返回群列表'''
    
    def newgroup(self, groupname):
        '''新建空群'''
        gpath = './grouplist/'
        if os.path.isfile(gpath + groupname):
            print groupname, u'该群已存在'
        else:
            tmpJsonFile = open(gpath + groupname,'w')
            tmpJsonFile.close()
            print groupname, u' 建群成功'
        self.lsGroup()
        
    def rmgroup(self, groupname):
        '''删除群'''
        gpath = './grouplist/'
        if os.path.isfile(gpath + groupname):
            os.remove(gpath + groupname)
            print u'成功删除群 ',groupname
        else:
            print u'群',groupname,u'不存在'
        self.lsGroup()
           
            
    def reNamegp(self, oldname, newname):
        '''群改名'''
        gpath = './grouplist/'
        if os.path.isfile(gpath + oldname):
            if os.path.isfile(gpath + newname):
                print u'新名称 ',newname,u' 已存在，不可改成此名称'
            else:
                os.rename(gpath + oldname, gpath + newname)
                print oldname, u' 群名称已成功更改为 ',newname
        else:
            print u'群',oldname,u'不存在'
        self.lsGroup()
    
    
    def lsUseringp(self, groupname):
        '''展示群成员'''
        if os.path.isfile('./grouplist/'+groupname):
            datalist = self.openGrouplist(groupname)
            print groupname, u' 群成员为：(',len(datalist),')'
            if len(datalist) == 0:
                print groupname, u'此群中暂无成员'
            else:
                for nameingroup in datalist:
                    print nameingroup.encode('utf-8')
            return datalist
            '''返回群内成员名单'''
        else:
            print u'群',groupname,u'不存在'
            return []
            
    def addUseringp(self, groupname, datalist):
        '''
        作用：向群中添加群成员
        参数：群名称， 用户列表
        '''
        if os.path.isfile('./grouplist/'+groupname):
            templist = self.openGrouplist(groupname)
            for userdata in datalist:
                if self.getUSerID(userdata):
                    if userdata in templist:
                        print userdata,u' 已存在于此群中'
                    else:
                        templist.append(userdata)
                        self.storeGrouplist(groupname, templist)
                        print userdata, u' 已添加成功'
                else:
                    print userdata,u' 该用户不存在'
        else:
            print u'群',groupname,u'不存在'
        self.lsUseringp(groupname)
    
    
    def rmUseringp(self, groupname, datalist):
        '''
        作用：删除群中特定群成员
        参数：群名称， 用户列表
        '''
        if os.path.isfile('./grouplist/'+groupname):
            templist = self.openGrouplist(groupname)
            for userdata in datalist:
                if self.getUSerID(userdata):
                    if userdata in templist:
                        #print userdata,' 已存在于此群中'
                        templist.remove(userdata)
                        self.storeGrouplist(groupname, templist)
                        print userdata, u' 已删除成功'
                    else:
                        print userdata, u' 不在此群中'
                else:
                    print userdata,u' 该用户不存在'
        else:
            print u'群',groupname,u'不存在'
        self.lsUseringp(groupname)
    
    def copyGroup(self, fromgp, togp):
        '''将前一个群的用户列表拷贝到后一个群中，不出现重复'''
        gpath = './grouplist/'
        if os.path.isfile(gpath + fromgp):
            if os.path.isfile(gpath + togp):
                listfrom = self.openGrouplist(fromgp)
                listto = self.openGrouplist(togp)
                listto.extend(listfrom)
                listto = list(set(listto))
                self.storeGrouplist(togp, listto)
                print u'已成功将群 ', fromgp, u' 拷贝到群 ', togp ,u' 中'
                self.lsUseringp(togp)
            else:
                print u'群',togp,u'不存在'
        else:
            print u'群',fromgp,u'不存在'
    
    def timeMsg(self,name,timer_flag,word):       
        pass 