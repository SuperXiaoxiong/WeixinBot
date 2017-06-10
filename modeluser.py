#coding:utf-8
'''
Created on 2017年2月15日
@author: superxiaoxiong
'''


'''
TODO :
:好友
:页面整理及归并
:说明文档
'''

import web
import wxlogin 
import threading
import os
import hashlib
import time
import MySQLdb
import re
import Queue
import datetime
import json

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class WXLoginTh(wxlogin.WXLogin):
    
    def __init__(self, serialnum, wx_id):
        super(WXLoginTh, self).__init__()
        
        self.serialnum =serialnum
        self.saveFolder = os.path.join(os.getcwd(), 'static')
        self.wx_id = wx_id
        
        

    def genQRCode(self):
        '''
        生成二维码，添加在linux平台下调用xdg打开二维码
        '''
        url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
        params = {
            't': 'webwx',
            '_': int(wxlogin.time.time()),
        }
        '''
        request = wxlogin.urllib2.Request(url=url, data=wxlogin.urllib.urlencode(params))
        response = wxlogin.urllib2.urlopen(request)
        data = response.read()
        '''
        response = self.req.post(url=url, data=wxlogin.urllib.urlencode(params))
        data = response.content
        #print data
        self._saveFile('qrcode'+ str(self.serialnum) +'.jpg', data)
        
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
            if not self.waitForLogin():
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
        
    def listenMsgMode(self):
        print u'[*] 进入消息监听模式 ... 成功'
        #logging.debug(u'[*] 进入消息监听模式 ... 成功')
        self._run(u'[*] 进行同步线路测试 ... ', self.testsynccheck)
        playWeChat = 0
        redEnvelope = 0
        
        
        
        
        while True:
            print 'is on job ' + str(self.serialnum)
            self.lastCheckTs = time.time()
            [retcode, selector] = self.synccheck()
            print 'retcode: %s, selector: %s, I am %d'  % (retcode, selector, self.serialnum)
            if self.DEBUG:
                print 'retcode: %s, selector: %s' % (retcode, selector)
            #logging.debug('retcode: %s, selector: %s' % (retcode, selector))
            if retcode == '1100':
                print '[*] 你在手机上登出了微信，债见'
                #logging.debug('[*] 你在手机上登出了微信，债见')
                break
            if retcode == '1101':
                print '[*] 你在其他地方登录了 WEB 版微信，债见'
                #logging.debug('[*] 你在其他地方登录了 WEB 版微信，债见')
                break
            if retcode == '1102':
                '''
                可能是sync节点需要更换
                '''
                self.testsynccheck()
                
            elif retcode == '0':
                if selector == '2':
                    print 'I get something' + str(self.serialnum)
                    r = self.webwxsync()
                    if r is not None:
                        self.handleMsg(r)
                elif selector == '6':
                    # TODO
                    r = self.webwxsync() #一面消息老刷屏
                    redEnvelope += 1
                    print '[*] 收到疑似红包消息 %d 次' % redEnvelope
                    #logging.debug('[*] 收到疑似红包消息 %d 次' % redEnvelope)
                elif selector == '7':
                    playWeChat += 1
                    print '[*] 你在手机上玩微信被我发现了 %d 次' % playWeChat
                    #logging.debug('[*] 你在手机上玩微信被我发现了 %d 次' % playWeChat)
                    r = self.webwxsync()
                elif selector == '0':
                    time.sleep(1)
                else:
                    r = self.webwxsync()
            time.sleep(1)
            if (time.time() - self.lastCheckTs) <= 20:
                time.sleep(time.time() - self.lastCheckTs)  
                
          

    def _showMsg(self, message):

        srcName = None
        dstName = None
        groupName = None
        content = None

        msg = message

        if msg['raw_msg']:
            srcName = self.getUserRemarkName(msg['raw_msg']['FromUserName'])
            dstName = self.getUserRemarkName(msg['raw_msg']['ToUserName'])
            content = msg['raw_msg']['Content']
            
            content = content.replace( '&lt;', '<').replace('&gt;', '>')
            message_id = msg['raw_msg']['MsgId']
           
            if msg['raw_msg']['FromUserName'][:2] == '@@':
                # 接收到来自群的消息
                if re.search(":<br/>", content, re.IGNORECASE):
                    [people, content] = content.split(':<br/>')
                    groupName = srcName
                    srcName = self.getUserRemarkName(people)
                    dstName = 'GROUP'
                else:
                    groupName = srcName
                    srcName = 'SYSTEM'
            elif msg['raw_msg']['ToUserName'][:2] == '@@':
                # 自己发给群的消息
                groupName = dstName
                dstName = 'GROUP'

            # 收到了红包
            if content == u'收到红包，请在手机上查看':
                msg['message'] = content

            # 指定了消息内容
            if 'message' in msg.keys():
                content = msg['message']
               
        if groupName != None:
            print '%s |%s| %s -> %s: %s' % (message_id, groupName.strip(), srcName.strip(), dstName.strip(), content)
        else:
            print '%s %s -> %s: %s' % (message_id, srcName.strip(), dstName.strip(), content)
            '''
            如果是自己发的消息recieved设为1
            反之为0
            '''
        if srcName == self.User['UserName']:
            sql = "insert into messagelist(srcName,dstName,content,wx_id,recieved) values ('"+srcName+"','"+dstName+"','"+content+ "','"+ str(self.wx_id) + "' ,+'1');"
        else:
            sql = "insert into messagelist(srcName,dstName,content,wx_id,recieved) values ('"+srcName+"','"+dstName+"','"+content+ "','"+ str(self.wx_id) + "', + '0');"    
        python_cur.execute(sql)
        #self.cur.close()
        python_conn.commit()
        print '插入成功！'
    
    
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
            if content.find('/cgi-bin/mmwebwx-bin/webwxgetpubliclinkimg') != -1:
                #收到群消息
                pass
            else:
                content = content.replace( '&lt;', '<').replace('&gt;', '>')
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
                
                
                  
                print msgType
                if msgType == 1:
                    self.q.put(r)
                    print 'qsize' + str(self.q.qsize())
                    raw_msg = {'raw_msg': msg}
                    self._showMsg(raw_msg)
                    #self.autoReplyMode = True
                    if msg['FromUserName'][:2] != '@@':
                        user_frilist = {
                        'wx_id':str(self.wx_id),
                        'markname':srcName
                        } 
                        
                        
                        '''
                        接收查询命令，读取日志文件
                        '''
                        #content = msg['Content']
                        #print "jinlaile"
                        print content
                        if(content[0:3] == 'cmd'):
                            cmd_read = content[4:].split(' ')
                            #print cmd_read
                            if len(cmd_read)== 4:
                                self.read_log(msg['FromUserName'],cmd_read[0],cmd_read[1],cmd_read[2],cmd_read[3],srcName)

                                                       
                        resultfrilist = db1.select('friend_list', what='privilege', where=web.db.sqlwhere(user_frilist) )
                        for i in resultfrilist:
                            if replyflag[self.wx_id][int(i.privilege)]==1:
                                ans = self._xiaodoubi(content) + u'\n[微信机器人自动回复]'
                                if self.webwxsendmsg(ans, msg['FromUserName']):
                                    db1.insert('messagelist',srcName='自动回复:',dstName=srcName,content=ans,wx_id=str(self.wx_id))
                                    print u'自动回复: ' + ans
                                else:
                                    print u'自动回复失败'
                    
                        
                        
                elif msgType == 37:
                    '''好友验证消息'''
                    print u'收到消息'
                    url = '%s/webwxverifyuser?r=%s&pass_ticket=%s' % (
                        self.base_uri , int(time.time()), self.pass_ticket)
                    data = {
                        'BaseRequest': self.BaseRequest,
                        'Opcode': msg['Status'], 
                        'VerifyUserListSize': 1,
                        'VerifyUserList': [{
                            'Value': msg['RecommendInfo']['UserName'],
                            'VerifyUserTicket': '', }],
                        'VerifyContent': msg['Ticket'],
                        'SceneListCount': 1,
                        'SceneList': [33], 
                        'skey': self.skey }
                    
                    self._post(url, data, True)
                    print url
                    print data
                    
                    self.webwxgetcontact()
                    
                    
                    
                    
                elif msgType == 10002:
                    raw_msg = {'raw_msg': msg, 'message': u'%s 撤回了一条消息' % srcName}
                    self._showMsg(raw_msg)
                else:
                    raw_msg = {
                        'raw_msg': msg, 'message': u'[*] 该消息类型为: %d，可能是表情，图片, 链接或红包' % msg['MsgType']}
                    #self._showMsg(raw_msg)       

    def read_log(self,FromUserName,machine_num,command,log_timedate,log_time,toName):
        
        path = './'+machine_num+'/'+command+log_timedate+'.txt'
        #print path
        temp=0
        flag =0

        if os.path.exists(path):
            logfile = open(path,"r")
            line = logfile.readline()
            print line
            while line:
                if line.find(log_time)!=-1:
                    while line and temp <5:
                        self.webwxsendmsg(line, FromUserName)

                        db1.insert('messagelist',srcName='记录查询:',dstName=toName,content=line,wx_id=str(self.wx_id))
                        flag = 1

                        temp +=1
                        line = logfile.readline()
                    break
                line = logfile.readline()
            logfile.close()

        if flag ==0 :
            self.webwxsendmsg('no record!', FromUserName)
            db1.insert('messagelist',srcName='记录查询:',dstName=toName,content='no record!',wx_id=str(self.wx_id))

            
urls = (
    '/(.*)/','redirect',
    '/login', 'login',
    '/logout', 'logout',
    '/regist','regist',
    '/index','index',
    '/group','group',
    '/messagelist','messagelist',
    '/changelevel','changelevel',
    '/levelreply','levelreply',
    '/friend','op_friend',
    '/api_get_message','api_get_messages',
    '/api_change_level','api_change_level',
    '/api_levelreply','api_levelreply',
    '/api_groupsend','api_groupsend',
    '/api_sendmsg','api_sendmsg', 
    '/api_monitor','api_monitor',
    )


def notfound():
    return web.seeother('./index')

app = web.application(urls, globals())
app.notfound = notfound




from random import Random
def random_str(randomlength=25):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str

    
def logged():
    
    if session.login == 1:
        return True
    else:
        return False
    


def create_render(privilege):  
    '''
    根据权限不同返回不同的页面
    '''
    if logged():
        if privilege == 0:     
            render = web.template.render('templates')
            
        elif privilege == 1:
            #用户权限
            pass
        elif privilege == 2:
            #游客
            render = web.template.render('templates')
            
    else:
        render = web.template.render('templates')
        
    
    return render

def calc_md5(password):
    md5_pass = hashlib.md5()
    md5_pass.update(password)
    return md5_pass.hexdigest()

class redirect:
    def GET(self, path):
        web.seeother('/'+ path)
        #print path
'''
class StaticFile:  
    def GET(self, file):  
        web.seeother('/static/'+file);
'''
class index:
    
    def GET(self):
        '''
        如果没有登录，重定向到登录页面
        如果登录，
            1.如果serialnum为-1，代表没有微信进程加入wxlogin进程，static存储二维码并按username存储，返回给用户，
            用户扫描二维码稍后返回聊天记录
            2.如果serialnum不为-1，代表进程存在，稍后返回聊天记录
        '''
        if logged():
            render = create_render(session.privilege)           
            if session.user.serialnum == -1:
                serialnum = len(wx_thread)
                wx_thread.append(serialnum)
                webwx = WXLoginTh(serialnum, session.user.id)
                webwx.getUUID()
                session.uuid = webwx.uuid
                webwx.genQRCode()
                db1.update('example_users', web.db.sqlwhere({'user':session.user.user}), serialnum=serialnum)
                session.user.serialnum = serialnum
                return "%s" % (render.index(session.user.user, './static/qrcode' + str(serialnum) +'.jpg', status='start'))
            
            else:
                '''
                wxkey 为default说明没有分配线程，需要创建监听线程线程
                不为default说明线程已经分配，查看wx_thread[serialnum]线程状态，返回线程状态
                '''
                if session.user.wxkey == 'default':
                    webwx = WXLoginTh(session.user.serialnum, session.user.id)
                    webwx.uuid = session.uuid
                    while True:
                        print u'[*] 请使用微信扫描二维码以登录 ... '
                        if not webwx.waitForLogin():
                            continue
                            print u'[*] 请在手机上点击确认以登录 ... '
                        if not webwx.waitForLogin():
                            continue
                        break
                    
                    webwx._run(u'[*] 正在登录 ... ', webwx.login)
                    webwx._run(u'[*] 微信初始化 ... ', webwx.webwxinit)
                    webwx._run(u'[*] 开启状态通知 ... ', webwx.webwxstatusnotify)
                    webwx._run(u'[*] 获取联系人 ... ', webwx.webwxgetcontact)
                    webwx._echo(u'[*] 应有 %s 个联系人，读取到联系人 %d 个' %
                               (webwx.MemberCount, len(webwx.MemberList)))
                    webwx._echo(u'[*] 共有 %d 个群 | %d 个直接联系人 | %d 个特殊账号 ｜ %d 公众号或服务号' % (len(webwx.GroupList),
                                                                                     len(webwx.ContactList), len(webwx.SpecialUsersList), len(webwx.PublicUsersList)))
                    
                    
                    t_listen = threading.Thread(target=webwx.listenMsgMode,args = ())
                    t_listen.start()
                    
                    wx_thread[session.user.serialnum] = t_listen
                    wx_list.append(webwx)
                    q_timer.put(timerJob(9997141980,'test','test',session.user.id))					
                    replyflag[session.user.id]=[0,0,0]					
                    '''
                    获取用户好友列表
                    '''
                    user_frilist = {
                        'wx_id':session.user.id
                    }
                    frienduserlist = webwx.ContactList
                    frienduser_full_name_list = []
                    
                    sql_friendlist =[]
        
                    tempsqllist = db1.select('friend_list',what='markname',where=web.db.sqlwhere(user_frilist))
                    for x in tempsqllist:
                        sql_friendlist.append(x.markname)
                        
        
                    for tempuser in frienduserlist:
                        '''
                        #更新好友列表
                        '''
                        temp2 = db1.transaction()       
                        if tempuser['RemarkName'] is None:
                            tempmark = tempuser['NickName']
                            frienduser_full_name_list.append(tempuser['NickName'])
                        else:
                            tempmark = tempuser['RemarkName']
                            frienduser_full_name_list.append(tempuser['RemarkName'])
                            
                        try:
                            if tempmark not in sql_friendlist:
                                db1.insert('friend_list',markname=tempmark,wx_id=session.user.id)
                                sql_friendlist.append(tempmark)
                        except :
                            temp2.rollback()
                        else:
                            temp2.commit()
                        
                            
                    sql_friendlist =[]
                    tempsqllist = db1.select('friend_list',what='markname',where=web.db.sqlwhere(user_frilist))
                    for friend in tempsqllist:
                        if friend.markname  not in frienduser_full_name_list:
                            delete_list = {
                                'markname':friend.markname,
                                }
                            db1.delete('friend_list',where=web.db.sqlwhere(delete_list))
                            
                    session.user.wxkey = random_str()
                    db1.update('example_users', web.db.sqlwhere({'user':session.user.user}), serialnum=session.user.serialnum, wxkey=session.user.wxkey)
                    return "%s" % (render.index0(session.user.user, 'none', status=session.user.wxkey))
                
                else:
                    '''
                    如果线程在运行，返回ok
                    线程没有运行，重置serialnum为-1，wxkey=default
                    '''
                    if wx_thread[session.user.serialnum].isAlive():
                        print session.user.serialnum
                        return "%s" % (render.index0(session.user.user, 'none', status=session.user.wxkey))
                    else:
                        db1.update('example_users', web.db.sqlwhere({'user':session.user.user}), serialnum=-1, wxkey='default')
                        session.user.serialnum = -1
                        session.user.wxkey = 'default'
                        web.seeother('/index')
            
        
        else:
            render = create_render(2)
            return "%s" % (render.login())
            pass
        
        
class op_friend:
    def GET(self):
        if logged():
            '''
                    获取用户好友列表
            '''
            serialnum = session.user.serialnum
            webwx = wx_list[serialnum]
            user_frilist = {
                'wx_id':session.user.id
            }
            webwx.webwxgetcontact()
            frienduserlist = webwx.ContactList
            frienduser_full_name_list = []
            
            sql_friendlist =[]

            tempsqllist = db1.select('friend_list',what='markname',where=web.db.sqlwhere(user_frilist))
            for x in tempsqllist:
                sql_friendlist.append(x.markname)
                

            for tempuser in frienduserlist:
                '''
                #更新好友列表
                '''
                temp2 = db1.transaction()       
                if tempuser['RemarkName'] is None:
                    tempmark = tempuser['NickName']
                    frienduser_full_name_list.append(tempuser['NickName'])
                else:
                    tempmark = tempuser['RemarkName']
                    frienduser_full_name_list.append(tempuser['RemarkName'])
                    
                try:
                    if tempmark not in sql_friendlist:
                        db1.insert('friend_list',markname=tempmark,wx_id=session.user.id)
                        sql_friendlist.append(tempmark)
                except :
                    temp2.rollback()
                else:
                    temp2.commit()
                
                    
            sql_friendlist =[]
            tempsqllist = db1.select('friend_list',what='markname',where=web.db.sqlwhere(user_frilist))
            for friend in tempsqllist:
                if friend.markname  not in frienduser_full_name_list:
                    delete_list = {
                        'markname':friend.markname,
                        }
                    db1.delete('friend_list',where=web.db.sqlwhere(delete_list))
                
                
               
            
            web.seeother('/group') 
        else:
            render = create_render(2)
            return "%s" % (render.login())    
            
                    
class login:
    
    def GET(self):
        '''
        如果已经登录，重定向到index.html
        没有登录，重定向到login.html
        '''
        if logged():
            render = create_render(session.privilege)
            print 'login '  + str(session.privilege)
            return "%s" % (render.index())
        else:
            render = create_render(2)
            return "%s" % (render.login())
    
    def POST(self):
        '''     
        从表单中得到example_user对应的数据  
        验证通过,重定向到index.html
        验证不通过,重定向到login.html
      '''  
        user_name = web.input().user
        passwd = web.input().passwd
        
        md5_passwd = calc_md5(passwd)
        user_login = {
            'user':user_name,
            'passwd':md5_passwd
            }
        sql = "select * from example_users where user =  %s  and passwd = %s ;" 
        print sql
        #python_cur.execute(sql,[user_name ,md5_passwd])
        
        #raw_results =  python_cur.fetchall()
        
        #print raw_results
        
        
        results = db1.select('example_users',  where=web.db.sqlwhere(user_login) )
        #数据库查询
        if len(results) == 1:
            #代表用户名密码验证正确
            user = results[0]
            session.login = 1
            session.privilege = user.privilege
            render = create_render(session.privilege)
            session.user = user
            web.seeother('/index')
        else:
            session.login = 0
            session.privilege = 2
            render = create_render(session.privilege)
            return "%s" % (render.login())
    
    
    
class logout:
    def GET(self):
        if logged():
            session.login = 0
            session.kill()
            web.seeother('/login')
        else:
            render = create_render(2)
            return "%s" % (render.login())



class regist:
    '''
    注册用户页面
    '''
    def GET(self):
        '''
        如果已经登录,将用户下线，再重定向到注册页面
        如果没有登录,返回注册表单
        '''
        if logged():
            session.login = 0
            session.kill()
            render = create_render(2)
            return "%s" % (render.regist())
        else:
            render = create_render(2)
            return "%s" % (render.regist())
        
    def POST(self):
        '''
        如果已经登录,重定向到注册页面,(继而下线)
        如果没有登录,进行用户注册:注册成功,重定向到index
                注册未成功,重定向到登录页面
        '''
        if logged():
            render = create_render(2)
            return "%s" % (render.regist())
        else:
            user_name = web.input().user
            passwd = web.input().passwd
            t = db1.transaction()
            md5_passwd = calc_md5(passwd)
            try:
                db1.insert('example_users',user=user_name, passwd=md5_passwd)
            except :
                t.rollback()
                render = create_render(2)
                return "%s" % (render.regist())
            else:
                t.commit()
                render = create_render(2)
                return "%s" % (render.login())
            

                       
class group: 
    #replyflag=[0,0,0]
    def GET(self):
        '''
        如果没有登录，重定向到登录页面
        如果登录，a
            
        '''
        if logged():
            render = create_render(session.privilege)     

            user_frilist0 = {
                'privilege':0,
                'wx_id':session.user.id
            }
            tempresultlist0 = db1.select('friend_list',what='markname',where=web.db.sqlwhere(user_frilist0) )
            restr0=''
            for x0 in tempresultlist0:
                restr0 = restr0 +' '+ x0.markname
            
        
            user_frilist1 = {
                'privilege':1,
                'wx_id':session.user.id
                }            
            tempresultlist1 = db1.select('friend_list',what='markname',where=web.db.sqlwhere(user_frilist1))
            restr1=''
            for x1 in tempresultlist1:
                restr1 = restr1 +' '+ x1.markname
            
            user_frilist2 = {
                'privilege':2,
                'wx_id':session.user.id
                    }            
            
            tempresultlist2 = db1.select('friend_list',what='markname',where=web.db.sqlwhere(user_frilist2))
            restr2=''
            for x2 in tempresultlist2:
                restr2 = restr2 +' '+ x2.markname
            #print 'GET',replyflag
            return render.group(restr0,restr1,restr2,replyflag[session.user.id][0],replyflag[session.user.id][1],replyflag[session.user.id][2])
        else:
            render = create_render(2)
            return "%s" % (render.login())
    def POST(self):  
        if logged():      		
            i = web.input(level=[])
            ckboxvalue = i.get('level')
            gpMsg = web.input().gpcontent
            
            if gpMsg != '':
                for i in ckboxvalue:
                    user_gplist = {
    					'wx_id':session.user.id,
                        'privilege':i
                    }
    
                    resultgplist = db1.select('friend_list',where=web.db.sqlwhere(user_gplist))
                    serialnum = session.user.serialnum
                    webwx = wx_list[serialnum]
                    srcName = '我'
                    for x in resultgplist:
                        sendMsg_result = webwx.sendMsg(x.markname, gpMsg)
                        if(sendMsg_result == 1):
                            db1.insert('messagelist',srcName=srcName,dstName=x.markname,content=gpMsg,wx_id=session.user.id)
            web.seeother('/group')        
        else:
            render = create_render(2)
            return "%s" % (render.login())

class api_groupsend:
    '''
        api功能：向特定级别发送消息
        输入格式如：[0,1,2]，消息内容和wxkey
        return json格式，
        返回格式
        {level:[0,1,2],
        message:消息内容
        }
    '''
    def POST(self):
        api_wxkey = web.input().wxkey
        x = web.input(level=[])
        ckboxvalue = x.get('level')
        gpMsg = web.input().gpcontent
        
        
        sql_select_id = 'select * from example_users where wxkey=$wxkey'
        idlists = db1.query(sql_select_id, vars={'wxkey':api_wxkey})
        for i in idlists:
            wxid = i.id
            wxserialnum = i.serialnum
             
        
        if gpMsg != '':
            for i in ckboxvalue:
                
                sql_select_fri = 'select * from friend_list where wx_id=(select id from example_users where wxkey=$wxkey) and privilege=$i'
                resultgplist = db1.query(sql_select_fri, vars={'wxkey':api_wxkey,'i':i})

                webwx = wx_list[wxserialnum]
                srcName = '我'
                for x in resultgplist:
                    dstName=x.markname
                    sendMsg_result = webwx.sendMsg(dstName, gpMsg)
                    if(sendMsg_result == 1):
                        sql_insert = 'insert into messagelist (srcName,dstName,content,wx_id) values ($srcName,$dstName,$content,$wx_id);'
                        db1.query(sql_insert, vars={'srcName':srcName,'dstName':dstName,'content':gpMsg,'wx_id':wxid})
        
        dict_msg = {
            "level" : ckboxvalue,
            "message":gpMsg,
            }
        return json.loads(json.dumps(dict_msg))


class api_levelreply:
    def POST(self):
        '''
        api功能：更改特定级别的自动回复状态
        输入格式如：[0,1,2]和wxkey
        return json格式，
        返回格式[flag0,flag1,flag2]
        '''
        
        api_wxkey = web.input().wxkey
        x = web.input(reply=[])
        replybox=x.get('reply')
        
        sql_select = 'select id from example_users where wxkey=$wxkey'
        messagelists = db1.query(sql_select, vars={'wxkey':api_wxkey})
        for i in messagelists:
            wxid = i.id
        #print replybox
        for tempre in replybox:
            #print tempre
            replyflag[wxid][int(tempre)] = (replyflag[wxid][int(tempre)]+1)%2
        
        return json.loads(json.dumps(replyflag[wxid]))


class levelreply:
    def POST(self):
        x = web.input(reply=[])
        replybox=x.get('reply') 
        #print replybox
        for tempre in replybox:
            #print tempre
            replyflag[session.user.id][int(tempre)] = (replyflag[session.user.id][int(tempre)]+1)%2
        #print 'POST',replyflag
        web.seeother('/group')


class api_change_level:
    def POST(self):
        '''
        api功能：更改用户级别
        
        return json格式，
        返回格式{
        true或者false
        }
        '''
        
        api_wxkey = web.input().wxkey
        username = web.input().username
        listvalue = web.input().choose_list
        
        temp2 = db1.transaction()
        try:
            sql_select = 'select * from friend_list where  markname=$markname and wx_id=(select id from example_users where wxkey=$wxkey)'
            resultfrilist = db1.query(sql_select, vars={'wxkey':api_wxkey,'markname':username})
            #数据库查询
            if len(resultfrilist) == 1:
                #该用户已存在
                #print username
                sql_update = 'update table friend_list set privilege=$listvalue where markname=$markname and wx_id=(select id from example_users where wxkey=$wxkey)'
                db1.query(sql_select, vars={'wxkey':api_wxkey,'markname':username,'listvalue':listvalue})
                                
        except :
            temp2.rollback()
            return json.loads(json.dumps(['false']))
        else:
            temp2.commit()
        
        return json.loads(json.dumps(['true']))
        

class changelevel:
    def POST(self):
        username = web.input().username
        listvalue = web.input().choose_list
        temp2 = db1.transaction()
        try:
            user_frilist = {
                'wx_id':session.user.id,
                'markname':username
            }                                
            resultfrilist = db1.select('friend_list',  where=web.db.sqlwhere(user_frilist) )
           
            #数据库查询
            if len(resultfrilist) == 1:
                #该用户已存在
                #print username
                db1.update('friend_list',where=web.db.sqlwhere(user_frilist),privilege=listvalue)
                #print listvalue
            else:
                pass
                                
        except :
            temp2.rollback()
        else:
            temp2.commit()
        web.seeother('/group')



        
class api_get_messages:
    def POST(self):
        '''
        api功能：获取消息。已经发送过得消息recieved位置为1，未发送置为0
        
        return json格式，
        返回格式{
        "length":长度，
        "messagelists":[
        [srcName1, dstName1, content1],
        [srcName2, dstName2, content2],
                ]
        }
        '''
        
        
        api_wxkey = web.input().wxkey
        sql_select = 'select srcName,dstName,content from messagelist where recieved=0 and wx_id=(select id from example_users where wxkey=$wxkey)'
        messagelists = db1.query(sql_select, vars={'wxkey':api_wxkey})
        sql_update = 'update  messagelist set recieved=1 where wx_id=(select id from example_users where wxkey=$wxkey)'
        db1.query(sql_update, vars={'wxkey':api_wxkey})          
                   
        msglists = []
        for msg in messagelists :
            msglist = [msg.srcName.encode('utf-8') , msg.dstName.encode('utf-8'), msg.content.encode('utf-8')] 
            msglists.append(msglist)
            
        dict_msg = {
            "length" : len(msglists),
            "messagelists":msglists,
            }
        print dict_msg
        msglist = json.dumps(dict_msg)
        return json.loads(msglist)           


class api_sendmsg:
    '''
    api功能：发送消息
    输入格式：｛'wxkey':wxkey,
        'dstName':dstName,
        'content':content,
        'timeflag':timeflag,--------------[]或[]
        'timerinfo':timerinfo-----------如22:13
        ｝
        
    return json格式，
    返回格式{
        'srcName':srcName,
        'dstName':dstName,
        'content':content,
        'timeMsg':timeMsg,
        'timerinfo':timerinfo
        }
    '''
    def POST(self):
        api_wxkey = web.input().wxkey
        
        sql_select_id = 'select * from example_users where wxkey=$wxkey'
        idlists = db1.query(sql_select_id, vars={'wxkey':api_wxkey})
        for i in idlists:
            wxid = i.id
            wxserialnum = i.serialnum
            
        dstName = web.input().dstName
        content = web.input().content
        timerinfo = web.input().timerinfo
        i = web.input(timeflag=[])
        ckboxvalue = i.get('timeflag')
        if len(ckboxvalue):
            timeMsg = '1'
        else:
            timeMsg = '0'
        webwx = wx_list[wxserialnum]
        
        srcName = '我'
        
        if timeMsg == '1':
            '''
            作用：定时发送特定人的消息
            格式：输入定时:人名:时间:信息；时间写小时:分钟就行，默认当天发送
            '''
            now_time = time.time()
            ltime = time.localtime(now_time)
            year = int(ltime.tm_year)
            mon = int(ltime.tm_mon)
            mday = int(ltime.tm_mday)
            hour = int(timerinfo.split(':')[0])
            min = int(timerinfo.split(':')[1])
            sec = 0
            timeC = datetime.datetime(year,mon,mday,hour,min,sec)
            timestamp = time.mktime(timeC.timetuple())
            q_timer.put(timerJob(timestamp,dstName,content,wxserialnum))
            print timestamp,dstName,content,wxserialnum
            lastest_timer = int(timestamp)
            
        elif timeMsg == '0':
            
            sendMsg_result = webwx.sendMsg(dstName, content)
            if(sendMsg_result == 1):
                sql_insert = 'insert into messagelist (srcName,dstName,content,wx_id) values ($srcName,$dstName,$content,$wx_id);'
                db1.query(sql_insert, vars={'srcName':srcName,'dstName':dstName,'content':content,'wx_id':wxid})
        dict_msg = {
            'srcName':srcName,
            'dstName':dstName,
            'content':content,
            'timeMsg':timeMsg,
            'timerinfo':timerinfo
            }
        return json.loads(json.dumps(dict_msg))
    
class messagelist: 
    def GET(self):
        '''
        如果没有登录，重定向到登录页面
        如果登录，a
            
        '''
        if logged():
            render = create_render(session.privilege)   
            
            user_frilist0 = {
                'wx_id':session.user.id
            }

            tempresultlist = db1.select('messagelist',what='message_id,srcName,dstName,content',where=web.db.sqlwhere(user_frilist0))
            restr=''
            for x in tempresultlist:
                message_id = str(x.message_id)
                restr = restr +'+'+str(message_id.zfill(6)) + ':'+ x.srcName + '->'+x.dstName + ':'+ x.content
            return render.messagelist(restr) 
        else:
            render = create_render(2)
            return "%s" % (render.login())
    
    def POST(self):
        if logged():
            dstName = web.input().dstName
            content = web.input().content
            i = web.input(timeflag=[])
            ckboxvalue = i.get('timeflag')
            if len(ckboxvalue):
                timeMsg = '1'
            else:
                timeMsg = '0'
                
            serialnum = session.user.serialnum
            webwx = wx_list[serialnum]
                          
            if timeMsg == '1':
            #print 'sdajak'
                '''
                作用：定时发送特定人的消息
                格式：输入定时:人名:时间:信息；时间写小时:分钟就行，默认当天发送
                '''
                timerinfo = web.input().timeinfo
                now_time = time.time()
                ltime = time.localtime(now_time)
                year = int(ltime.tm_year)
                mon = int(ltime.tm_mon)
                mday = int(ltime.tm_mday)
                hour = int(timerinfo.split(':')[0])
                min = int(timerinfo.split(':')[1])
                sec = 0
                timeC = datetime.datetime(year,mon,mday,hour,min,sec)
                timestamp = time.mktime(timeC.timetuple())
                q_timer.put(timerJob(timestamp,dstName,content,session.user.serialnum))
                print timestamp,dstName,content,session.user.serialnum
                lastest_timer = int(timestamp)
            
            elif timeMsg == '0':
        #print dstName
                srcName = '我'
                sendMsg_result = webwx.sendMsg(dstName, content)
                if(sendMsg_result == 1):
                    db1.insert('messagelist',srcName=srcName,dstName=dstName,content=content,wx_id=session.user.id)
                
            
            
            web.seeother('/messagelist')      
        else:
            render = create_render(2)
            return "%s" % (render.login()) 


class timerJob(object):
    '''
    定时消息类，包括时间轴，收件人和发送的信息
    '''
    def __init__(self,priority,name,word,wxid):
        self.priority = priority
        self.name = name
        self.word = word
        self.wxid = wxid
        return
    def __cmp__(self,other):
        
        return cmp(self.priority,other.priority)
    

def process_timejob(q_timer):
    '''
    线程：监听离现在最近的定时消息是否可以发送
    计算时间方法：使用优先队列，每次取两个数据，比较时间轴，大的重新放回队列，然后短的时间轴
和现在的时间轴比较，小的话，重新放回队列，休眠一秒，循环此过程
这样可以保证随时输入的定时消息可以取出队列进行比较
    '''
    while True:
        while True:
            next_timejob = q_timer.get()
            next_next_timejob = q_timer.get()
            if next_next_timejob.priority < next_timejob.priority:
                q_timer.put(next_timejob)
                now_timejob = next_next_timejob
            else:
                q_timer.put(next_next_timejob)
                now_timejob = next_timejob
            
            if int(now_timejob.priority) <= int(time.time()):
                break
            else:
                time.sleep(1)
            q_timer.put(now_timejob) 
                
        serialnum = now_timejob.wxid
        print serialnum
        webwx = wx_list[serialnum]
        print serialnum,now_timejob.name, now_timejob.word
        webwx.sendMsg(now_timejob.name, now_timejob.word)
        q_timer.task_done()          
#replyflag = [0,0,0]
replyflag={}
                        
db1 = web.database(dbn = 'mysql', db='webuser', user='root',pw='root')  
wx_thread = []  
wx_list = []
q_timer = Queue.PriorityQueue()
time_work = threading.Thread(target=process_timejob,args=(q_timer,))
time_work.start()



'''
#--------数据库添加-------
使用python原生语句操作mysql数据库
'''
python_conn = MySQLdb.connect(host='localhost',port=3306,user='root',passwd = 'root',db='webuser')
python_cur = python_conn.cursor()
python_conn.set_character_set('utf8')
python_cur.execute('SET NAMES utf8;') 
python_cur.execute('SET CHARACTER SET utf8;')
python_cur.execute('SET character_set_connection=utf8;')
print '连接数据库成功！'




if web.config.get('_session') is None:
    session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'login':0})
    web.config._session = session
    print 1
else:
    print  2
    session = web.config._session

def init_session():
    cur_pwd = os.getcwd()
    cur_path = os.path.join(cur_pwd,'sessions')
    list_files = os.listdir(cur_path)
    for _file in list_files:
        os.remove(os.path.join(cur_path,_file))   



    

def init_db():
    #sql = "insert into messagelist(srcName,dstName,content,wx_id) values ('"+srcName+"','"+dstName+"','"+content+ "','"+ str(self.wx_id) + "');"
    sql = "update example_users set serialnum=-1, wxkey='default' where 1;"
    python_cur.execute(sql)
    python_conn.commit()
    print '执行'

    
if __name__ == "__main__":
    '''
    定义服务器重启 :
    删除session,
    数据库将wxkey全置为default,serialnum置为-1,但联系人,对话,group保留
    '''
    init_session()
    init_db()
    #使用uwsgi采用接口
    #application = app.wsgifunc() 
    app.run()


class api_monitor:
    def POST(self):
        api_wxkey = web.input().wxkey
        machine_num= web.input().machine_num
        x = web.input(level=[])
        ckboxvalue = x.get('level')
        cpu_state = json.loads(web.input().cpu_state)
        mem_state = json.loads(web.input().mem_state)
        proc_state = json.loads(web.input().proc_state)
#         print proc_state
#         print type(gpMsg)
#         print gpMsg
        
        path = machine_num
        if not os.path.exists(path):
            os.mkdir(path)
            
        else:
            print '目录已存在'
        
        time_today = time.strftime('%Y-%m-%d',time.localtime(time.time()))
        time_log = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time()))
        #time_i = datetime.datetime.now()
        #time_today = str(time_i.year)+str(time_i.month)+str(time_i.day)
        cpulogfile = open("./"+ path +"/cpu"+ time_today +".txt",'a')
        cpu_string = time_log + u': cpu占用比: '+ str(cpu_state["cpu_percent_sum"])\
        + u'%, 用户态cpu时间比: '+ str(cpu_state["cpu_user_sum"])\
        + u'ns, nice用户态cpu时间比: '+ str(cpu_state["cpu_nice_sum"])\
        + u'ns, 系统态cpu时间比: '+ str(cpu_state["cpu_system_sum"])\
        + u'ns, 空闲的cpu时间比: '+ str(cpu_state["cpu_idle_sum"])\
        + u'ns, cpu等待磁盘写入时间: '+ str(cpu_state["cpu_iowait_sum"])\
        + u'ns, 硬中断消耗时间: '+ str(cpu_state["cpu_irq_sum"])\
        + u'ns, 软中断消耗时间: '+ str(cpu_state["cpu_softirq_sum"])\
        + u'ns, 虚拟机偷取时间: '+ str(cpu_state["cpu_steal_sum"]) + '\n'
        cpulogfile.write(cpu_string)
        cpulogfile.close()
        
        memlogfile = open("./"+ path +"/mem"+ time_today +".txt",'a')
        mem_string = time_log + u': 内存占比: '+ str(mem_state["mem_percent"])\
        + u'%, 内存总量: '+ str(mem_state["mem_total"])\
        + u'M, 已用内存: '+ str(mem_state["mem_used"])\
        + u'M, 剩余内存: '+ str(mem_state["mem_free"])+ u'M\n'
        memlogfile.write(mem_string)
        memlogfile.close()
        
        proclogfile = open("./"+ path +"/proc"+ time_today +".txt",'a')
        for i in range(1,6):
            proc_name = "proc"+str(i)
            proc_string = time_log + u': 进程名称: '+ str(proc_state[proc_name]["name"])\
            + u' 占用内存: '+ str(proc_state[proc_name]["mem"])\
            + u'%, 占用cpu: '+ str(proc_state[proc_name]["cpu"])+ '\n'
            proclogfile.write(proc_string)
        proclogfile.close()
        
        
        sql_select_id = 'select * from example_users where wxkey=$wxkey'
        idlists = db1.query(sql_select_id, vars={'wxkey':api_wxkey})
        for i in idlists:
            wxid = i.id
            wxserialnum = i.serialnum
             
        
        if cpu_state["cpu_percent_sum"] > 25 or mem_state["mem_percent"] > 65:

            gpmsgcontent = time_log + u'机器　'+ machine_num +u'　状态异常: '
            if cpu_state["cpu_percent_sum"] > 25:
                gpmsgcontent +=u'cpu: '+str(cpu_state["cpu_percent_sum"])+'; '
            if mem_state["mem_percent"] > 65:
                gpmsgcontent +=u'mem: '+str(mem_state["mem_percent"])+'; '

                
            for i in ckboxvalue:
                sql_select_fri = 'select * from friend_list where wx_id=(select id from example_users where wxkey=$wxkey) and privilege=$i'
                resultgplist = db1.query(sql_select_fri, vars={'wxkey':api_wxkey,'i':i})

                webwx = wx_list[wxserialnum]
                srcName = '我'
                for x in resultgplist:
                    dstName=x.markname
                    sendMsg_result = webwx.sendMsg(dstName, gpmsgcontent)
                    if(sendMsg_result == 1):
                        sql_insert = 'insert into messagelist (srcName,dstName,content,wx_id) values ($srcName,$dstName,$content,$wx_id);'

                        db1.query(sql_insert, vars={'srcName':srcName,'dstName':dstName,'content':gpmsgcontent,'wx_id':wxid})

        
        dict_msg = {
            "level" : ckboxvalue,
            "mem_state":mem_state,
            "cpu_state":cpu_state,
            }
        return json.loads(json.dumps(dict_msg))