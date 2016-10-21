#coding:utf-8
'''
Created on 2016年10月6日
@author: 肖雄
'''

import web
from wxlogin import *
from pprint import pprint
import threading
import cmd

web.config.debug = False

urls = (
    '/text/','ManageApi',
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
        elif cmd[:10] == "sendgpmsg:":
            '''
            作用：发送群消息
            格式： sendgpmsg:groupname:word
            '''
            [groupname, word] = cmd[10:].split(':')
            logging.info((groupname + ':groupname,' + word + 'word').encode('utf-8'))
            webwx.sendGroupmsg(groupname, word)
        elif cmd == 'lsgp':
            '''
            作用：显示出所有群
            '''
            webwx.lsGroup()
        elif cmd[:6] =='newgp:':
            '''
            作用：新建空群
            格式：  newgp:groupname
            '''
            groupname = cmd[6:]
            webwx.newgroup(groupname)
        elif cmd[:9] =='renamegp:':
            '''
            作用：更改群名称
            格式：  renamegp:oldname:newname
            '''
            [oldname, newname] = cmd[9:].split(':')
            webwx.reNamegp(oldname, newname)
            
        elif cmd[:5] =='rmgp:':
            '''
            作用：删除群
            格式：  rmgp:groupname
            '''
            groupname = cmd[5:]
            webwx.rmgroup(groupname)
        elif cmd[:9] =='lsuserin:':
            '''
            作用：展示群中成员
            格式：  lsuserin:groupname
            '''
            groupname = cmd[9:]
            webwx.lsUseringp(groupname)
        elif cmd[:8] == 'adduser:':
            '''
            作用：向群中添加用户
            格式：   adduser:groupname:user1,user,user3......
            '''
            [groupname,data] = cmd[8:].split(':')
            datalist = data.split(',')
            webwx.addUseringp(groupname, datalist)
        elif cmd[:7] == 'rmuser:':
            '''
            作用：删除群中用户
            格式：   rmuser:groupname:user1,user,user3......
            '''
            [groupname,data] = cmd[7:].split(':')
            datalist = data.split(',')
            webwx.rmUseringp(groupname, datalist)
        elif cmd[:7] == 'copygp:':
            '''
            作用：复制群成员到另外一个群
            格式：来源群，  去向群
            '''
            [fromgpname, togpname] = cmd[7:].split(':')
            webwx.copyGroup(fromgpname, togpname)
            
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