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
url = 'http://127.0.0.1:8081/api_get_message'
wxkey = 'w7xkqHvAHVe9ALv7S4XjQEP02'
response = requests.post(url,data={'wxkey':wxkey})
print response.url
print response.content