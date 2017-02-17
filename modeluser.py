#coding:utf-8
'''
Created on 2017年2月15日
@author: superxiaoxiong
'''

import web
from WeixinBot import wxlogin 
import threading
import os

class WXLoginTh(wxlogin.WXLogin):
    
    def __init__(self, serialnum):
        super(wxlogin.WXLogin, self).__init__()
        
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
        request = wxlogin.urllib2.Request(url=url, data=wxlogin.urllib.urlencode(params))
        response = wxlogin.urllib2.urlopen(request)
        data = response.read()
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
        
        
            
urls = (
    '/(.*)/','redirect',
    '/login', 'login',
    '/logout', 'logout',
    '/regist','regist',
    '/index','index',
    )

app = web.application(urls, globals())

if web.config.get('_session') is None:
    session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'login':0})
    web.config._session = session
else:
    session = web.config._session
    
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


class redirect:
    def GET(self, path):
        web.seeother('/'+ path)
        #print path



class index:
    
    def GET(self):
        '''
        如果没有登录，重定向到登录页面
        如果登录，
            1.如果serialnum为-1，代表没有微信进程加入wxlogin进程，static存储二维码并按username存储，返回给用户，稍后返回聊天记录
            2.如果serialnum不为-1，代表进程存在，稍后返回聊天记录
        '''
        if logged():
            render = create_render(session.privilege)           
            #if session.user.serialnum == -1:
            '''
                webwx = WXLoginTh(session.user.serialnum)
                webwx.genQRCode()
                '''
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
            return "%s" % (render.index(session.user.user, './static/qrcode.jpg', status='ok'))
        
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
        user_login = {
            'user':user_name,
            'passwd':passwd
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
            try:
                db1.insert('example_users',user=user_name, passwd=passwd)
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