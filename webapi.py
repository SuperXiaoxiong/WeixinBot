#coding:utf-8
'''
Created on 2016年10月6日
@author: knight110
'''

import web
from wxlogin import *
from pprint import pprint
import threading

web.config.debug = False

urls = (
    '/text/','ManageApi',
    '/test/','Test'
    )



        
class ManageApi():
            
    def __init__(self):
        
        pass
       
            
    def GET(self):
        
        print 'qsize api' + str(webwx.q.qsize())
        print u'[*] 共有 %d 个群 | %d 个直接联系人 | %d 个特殊账号 ｜ %d 公众号或服务号' % (len(webwx.GroupList),len(webwx.ContactList), len(webwx.SpecialUsersList), len(webwx.PublicUsersList))
  
             
        if not webwx.q.empty():
            data = webwx.q.get()
            print(json.dumps(data, indent=4, ensure_ascii=False))
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
        
def input_cmd():
    while True:
        cmd = raw_input()
        cmd = cmd.decode(sys.stdin.encoding)
        if cmd == 'quit':
            
            print(u'[*] 退出微信')
            exit()
        elif cmd[:2] == '->':
            [name, word] = cmd[2:].split(':')
            logging.info((name + ':name,' + word + 'word').encode('utf-8'))
            webwx.sendMsg(name, word)
        elif cmd[:6] == 'reply:':
            a = cmd[6:]
            if int(a) == 1:
                webwx.reply_change(True)
            else:
                webwx.reply_change(False)   
        
            
if __name__ == '__main__':
    
    
    webwx = WXLogin()
    webwx.login_module()
    t_listen = threading.Thread(target=webwx.listenMsgMode,args = ())
    t_listen.setDaemon(True)
    t_listen.start()
    
    
    t_input = threading.Thread(target=input_cmd, args=())
    t_input.setDaemon(True)
    t_input.start()

    
    app = web.application(urls,globals())
    app.run()