#coding:utf-8
'''
Created on 2017年2月15日
@author: superxiaoxiong
'''

'''
TODO :
:API
 :群发定时 级别
 :自动回复  级别
 :插入数据库 发消息
 :判断为空 messagelist
 :index页面丰富
 :使用公网转发
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


class WXLoginTh(wxlogin.WXLogin):
    
    def __init__(self, serialnum, wx_id):
        super(WXLoginTh, self).__init__()
        
        self.serialnum =serialnum
        self.saveFolder = os.path.join(os.getcwd(), 'static')
        self.wx_id = wx_id
        
        #--------数据库添加-------
        '''
                    连接mysql数据库
        '''
        self.conn = MySQLdb.connect(host='localhost',port=3306,user='root',passwd = 'root',db='webuser')
        self.cur = self.conn.cursor()
        self.conn.set_character_set('utf8')
        self.cur.execute('SET NAMES utf8;') 
        self.cur.execute('SET CHARACTER SET utf8;')
        self.cur.execute('SET character_set_connection=utf8;')
        print '连接数据库成功！'
        #----------------------

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
            
            # content = msg['raw_msg']['Content'].replace(
            # '&lt;', '<').replace('&gt;', '>')
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
            # reload(sys)
            # sys.setdefaultencoding('utf-8')
            print '%s %s -> %s: %s' % (message_id, srcName.strip(), dstName.strip(), content)
            sql = "insert into messagelist(srcName,dstName,content,wx_id) values ('"+srcName+"','"+dstName+"','"+content+ "','"+ str(self.wx_id) + "');"
            self.cur.execute(sql)
            #self.cur.close()
            self.conn.commit()
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
                user_frilist = {
                'wx_id':str(self.wx_id),
                'markname':srcName
                }                                
                resultfrilist = db1.select('friend_list', what='privilege', where=web.db.sqlwhere(user_frilist) )
                for i in resultfrilist:
                    if replyflag[int(i.privilege)]==1:
                        ans = self._xiaodoubi(content) + u'\n[微信机器人自动回复]'
                        if self.webwxsendmsg(ans, msg['FromUserName']):
                            db1.insert('messagelist',srcName='自动回复:',dstName=srcName,content=ans,wx_id=str(self.wx_id))
                            print u'自动回复: ' + ans
                        else:
                            print u'自动回复失败'
                '''
                if groupName == None:
                    if self.autoReplyMode:
                        ans = self._xiaodoubi(content) + u'\n[微信机器人自动回复]'
                        if self.webwxsendmsg(ans, msg['FromUserName']):
                            db1.insert('messagelist',srcName='自动回复:',dstName=srcName,content=ans,wx_id=str(self.wx_id))
                            print u'自动回复: ' + ans
                        else:
                            print u'自动回复失败'
                 '''           
                '''
                if content[0:4] == u'cmd:':
                    cmd = content[4:]
                    #self.pipe.stdin.write(cmd)
                    #self.pipe.stdin.flush()
                    #self.cmder = msg['FromUserName']
                    
                    '''
            elif msgType == 37:
                '''好友验证消息'''
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
                    'SceneList': 33, 
                    'skey': self.skey }
                
                self._post(url, data, True)
                self.webwxgetcontact()
                
                
                
            elif msgType == 10002:
                raw_msg = {'raw_msg': msg, 'message': u'%s 撤回了一条消息' % srcName}
                self._showMsg(raw_msg)
            else:
                raw_msg = {
                    'raw_msg': msg, 'message': u'[*] 该消息类型为: %d，可能是表情，图片, 链接或红包' % msg['MsgType']}
                #self._showMsg(raw_msg)       

            
urls = (
    '/(.*)/','redirect',
    '/login', 'login',
    '/logout', 'logout',
    '/regist','regist',
    '/index','index',
    '/group','group',
    '/messagelist','messagelist',
    )


def notfound():
    return web.notfound("Sorry, the page you were looking for was not found.")

app = web.application(urls, globals())
app.notfound = notfound

if web.config.get('_session') is None:
    session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'login':0})
    web.config._session = session
else:
    session = web.config._session


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
					
					
                    '''
                    获取用户好友列表
                    '''
                    user_frilist = {
                        'wx_id':session.user.id
                    }
                    frienduserlist = webwx.ContactList
                    sql_friendlist =[]
                    tempsqllist = db1.select('friend_list',what='markname',where=web.db.sqlwhere(user_frilist))
                    for x in tempsqllist:
                        sql_friendlist.append(x.markname)
                        
                    for tempuser in frienduserlist:
                        '''
                        #更新好友列表
                        '''
                        temp2 = db1.transaction()
                        tempmark=tempuser['RemarkName']
                        try:
                            if tempmark not in sql_friendlist:
                                db1.insert('friend_list',markname=tempmark,wx_id=session.user.id)
                                sql_friendlist.append(tempmark)
                        except :
                            temp2.rollback()
                        else:
                            temp2.commit()
                    
                    
                    session.user.wxkey = random_str()
                    db1.update('example_users', web.db.sqlwhere({'user':session.user.user}), serialnum=session.user.serialnum, wxkey=session.user.wxkey)
                    return "%s" % (render.index(session.user.user, 'none', status='nice'))
                
                else:
                    '''
                    如果线程在运行，返回ok
                    线程没有运行，重置serialnum为-1，wxkey=default
                    '''
                    if wx_thread[session.user.serialnum].isAlive():
                        print session.user.serialnum
                        return "%s" % (render.index(session.user.user, 'none', status=session.user.wxkey))
                    else:
                        db1.update('example_users', web.db.sqlwhere({'user':session.user.user}), serialnum=-1, wxkey='default')
                        session.user.serialnum = -1
                        session.user.wxkey = 'default'
                        web.seeother('/index')
            '''
                初步思路，生成二维码，将二维码传回，页面传值wx对象
                '''
            '''
                t_listen = threading.Thread(target=webwx.listenMsgMode,args = ())
                t_listen.start()
                serialnum = len(wx_thread)
                wx_thread.append(t_listen)
                
                db1.update('example_users', web.db.sqlwhere({'user':session.user.user}), serialnum=serialnum)
                '''
                #return "%s" % (render.index(session.user.user, url = './static/qrcode.jpg', status='ok'))
          
                #return "%s" % (render.index(session.user.user, url = './static/qrcode'+str(session.user.serialnum)+'.jpg', status='ok'))
            #else:
            '''
                if wx_thread[session.user.serialnum].isAlive():
                
                    return "%s" % (render.index(session.user.user, status = 'ok', url=''))
                else:
                    return "%s" % (render.index(session.user.user, status = 'no', url =''))
                '''
            #return "%s" % (render.index(session.user.user, './static/qrcode.jpg', status='ok'))
        
        else:
            render = create_render(2)
            return "%s" % (render.login())
            pass
        
        
        
class login:
    
    def GET(self):
        '''
        如果已经登录，重定向到index.html
        没有登录，重定向到login.html
        '''
        if logged():
            render = create_render(session.privilege)
            return "%s" % (render.index())
        else:
            render = create_render(-1)
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
            render = create_render(2)
            return "%s" % (render.login())
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
            return render.group(restr0,restr1,restr2,replyflag[0],replyflag[1],replyflag[2])
        else:
            render = create_render(2)
            return "%s" % (render.login())
    def POST(self):
        username = web.input().username
        listvalue = web.input().choose_list		
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
        
        x = web.input(reply=[])
        replybox=x.get('reply') 
        #print replybox
        for tempre in replybox:
            #print tempre
            replyflag[int(tempre)] = (replyflag[int(tempre)]+1)%2
        #print 'POST',replyflag
        web.seeother('/group')        

           
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
                restr = restr +'+'+str(x.message_id) + ':'+ x.srcName + '->'+x.dstName + ':'+ x.content
            return render.messagelist(restr) 
        else:
            render = create_render(2)
            return "%s" % (render.login())
    
    def POST(self):

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
        reply_mode = web.input().choose_list
        if reply_mode == 'on':
            webwx.reply_change(True)
        elif reply_mode == 'off':
            webwx.reply_change(False) 
        else:         
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
replyflag = [0,0,0]
                        
db1 = web.database(dbn = 'mysql', db='webuser', user='root',pw='root')  
wx_thread = []  
wx_list = []
q_timer = Queue.PriorityQueue()
time_work = threading.Thread(target=process_timejob,args=(q_timer,))
time_work.start()

if __name__ == "__main__":
    
    app.run()