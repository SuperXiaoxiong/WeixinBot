#coding:utf-8
'''
Created on 2017年2月15日
@author: superxiaoxiong
'''

'''
二维码获取出现逻辑问题

'''

import web
import wxlogin 
import threading
import os
import hashlib
import time

class WXLoginTh(wxlogin.WXLogin):
    
    def __init__(self, serialnum):
        super(WXLoginTh, self).__init__()
        
        self.serialnum =serialnum
        self.saveFolder = os.path.join(os.getcwd(), 'static')
        
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
        QRCODE_PATH = self._saveFile('qrcode'+ str(self.serialnum) +'.jpg', data)
        
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
            
urls = (
    '/(.*)/','redirect',
    '/login', 'login',
    '/logout', 'logout',
    '/regist','regist',
    '/index','index',
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


'''

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
                webwx = WXLoginTh(serialnum)
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
                    webwx = WXLoginTh(session.user.serialnum)
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
                    serialnum = len(wx_thread)
                    wx_thread.append(t_listen)
                    
                    session.user.wxkey = random_str()
                    db1.update('example_users', web.db.sqlwhere({'user':session.user.user}), serialnum=serialnum, wxkey=session.user.wxkey)
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
        如果已经登录，重定向到login_double.html
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
            
            
            
            
                
db1 = web.database(dbn = 'mysql', db='webuser', user='root',pw='')  
wx_thread = []  
if __name__ == "__main__":
    
    app.run()