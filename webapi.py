#coding:utf-8
'''
Created on 2016年10月6日
@author: 肖雄
'''

import web
from wxlogin import *
from pprint import pprint
import threading

web.config.debug = False

urls = (
    '/msg/','MsgApi',
    '/reply/','AutoReplyApi',
    '/groupLists/','GroupListsApi',
    '/groupList','/GroupListApi',
    '/contactList','ContactListApi',
    )

class AutoReplyApi():
    '''
    AutoReplyApi 对自动回复状态进行操作
    GET 方法查看自动回复状态，返回json格式的自动回复状态
    POST 字段reply对自动回复状态进行更改，返回json格式的自动回复状态['操作boolean','状态']
    True为开启，False为关闭
    '''
    
    def GET(self):
        return json.dumps(webwx.autoReplyMode)

    
    def POST(self):
        data = web.data()
        data = data.decode('utf-8')
        data = json.loads(data)
        try:
            webwx.reply_change(data)
            return json.dumps([True,webwx.autoReplyMode])
        except:
            return json.dumps([False,webwx.autoReplyMode])

class GroupListsApi():
    '''
    GroupListsApi 对群进行增删改查操作
    GET 返回json格式['群数',[name1,name2,...]]
    POST 参数add(对应增加群srcname),del(删除群srcname),mvn(修改群srcname,dstname),返回json格式['操作boolean'.'群数',[name1,name2,...]]
    '''
    def GET(self):
        pass
    
    
    def POST(self):
        pass
    


class ContactListApi():
    '''
    返回联系人列表
    '''
    pass


class GroupListApi():
    '''
    GroupListApi 对单个群进行增删改查操作
    GET 返回json格式['人数',[name1,name2,...]]
    POST 参数 groupName,参数add(name),del(name),返回json格式['操作boolean',groupname,[name1,name2,...]]
    '''
    def GET(self):
        pass
    
    def POST(self):
        pass
    
        
class MsgApi():
            
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