#coding:utf-8
'''
Created on 2016年10月21日
@author: 肖雄
'''
'''

a = '中文'
print str(a)
print type(str(a)) 
import os
import sys
'''

'''
print isinstance(a,unicode)
lista = []
print type(lista)
print isinstance(lista, list)
'''
'''
from random import Random
def random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str

print random_str()
print random_str()
'''


'''
groups = os.listdir('./grouplist')
print u'当前群列表为：(',len(groups),')'
if len(groups) == 0:
    print u'暂无群发列表'
else:
    for f in groups:
        print type(f)
        print sys.getdefaultencoding()
        #print sys.stdin.encoding
        #print sys.getfilesystemencoding()
        a = f.decode(sys.getfilesystemencoding())
        print a.encode('utf-8')
   '''
   
import requests
# url = 'http://127.0.0.1:8081/api_get_message'
# wxkey = 'w7xkqHvAHVe9ALv7S4XjQEP02'
# response = requests.post(url,data={'wxkey':wxkey,'username':username})
# print response.url
# print response.content

# url = 'http://127.0.0.1:8080/api_change_level'
# wxkey = 'HHWoL1QDKZzzE2QXaMEzV803O'
# username = u'肖雄'
# choose_list = 1
# response = requests.post(url,data={'wxkey':wxkey,'username':username,'choose_list':choose_list})
# print response.url
# print response.content

# import json
# print json.loads(json.dumps(['true']))


# url = 'http://127.0.0.1:8080/api_levelreply'
# wxkey = 'QHELGEPliOEiSCpokC5aveqoe'
# reply = [0,1]
# response = requests.post(url,data={'wxkey':wxkey,'reply':reply})
# print response.url
# print response.content



# url = 'http://127.0.0.1:8080/api_groupsend'
# wxkey = 'ESjo9T5ibSxYjCR5rd892VRfk'
# level = [1]
# gpcontent=u'无聊'
# response = requests.post(url,data={'wxkey':wxkey,'level':level,'gpcontent':gpcontent})
# print response.url
# print response.content



url = 'http://127.0.0.1:8080/api_sendmsg'
wxkey = 'L8aJFj8h7chtLt0McPSyspzls'
dstName = u'肖雄'
content = u'再试一下定时'
timeflag = []
timerinfo = '17:14'
response = requests.post(url,data={'wxkey':wxkey,'dstName':dstName,'content':content,'timeflag':timeflag,'timerinfo':timerinfo})
print response.url
print response.content