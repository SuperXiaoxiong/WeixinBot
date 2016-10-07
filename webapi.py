#coding:utf-8
'''
Created on 2016年10月6日
@author: knight110
'''

import web
from wxlogin import *
from pprint import pprint

web.config.debug = False

urls = (
    '/text/','ManageApi',
    '/test/','Test'
    )


class Test():
    def __init__(self):
        
        print '1'*20
        
    def GET(self):
        print '2'*20
        num.add_num()
        return num.num
        #session.count.add_num()
        #print session.count.num
        #return str(session.count.num)
    
class CountNum():
    
    def __init__(self):
        self.num = 1
    
    def add_num(self):
        self.num = self.num + 1 
        
class ManageApi():
            
    def __init__(self):
        
        print '1'*10
       
            
    def GET(self):
        
            
        print 'GET2' * 10
        print 'qsize api' + str(webwx.q.qsize())
        print u'[*] 共有 %d 个群 | %d 个直接联系人 | %d 个特殊账号 ｜ %d 公众号或服务号' % (len(webwx.GroupList),len(webwx.ContactList), len(webwx.SpecialUsersList), len(webwx.PublicUsersList))
  
             
        if not webwx.q.empty():
            data = webwx.q.get()
            pprint(data)
            if data:
                #data = json.dump(data)
                return data
            else :
                return None
        else:
            return None
    
    def POST(self):
        data = web.data()
        data = data.decode('utf-8')
        pprint(data)
        data = json.loads(data)
        name = data['name']
        word = data['word']
        webwx.sendMsg(name, word)

if __name__ == '__main__':
    
    
    webwx = WXLogin()
    webwx.login_module()
    listenProcess = multiprocessing.Process(target=webwx.listenMsgMode)
    listenProcess.start()

    num = CountNum()
    print type(num)
    
    app = web.application(urls,globals())
    #session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})
    #session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': num})
    app.run()
    