#coding:utf-8
'''
Created on 2016年10月7日
@author: 肖雄
'''

import requests
import json
import pprint
import wxlogin

class ClientTest(object):
    
    def __init__(self):
        self.urltest = 'http://127.0.0.1:1234/test/'
        self.urltext = 'http://127.0.0.1:1234/text/'
        self.urlgrouplists = 'http://127.0.0.1:1234/groupLists/'
        self.urlgroup = 'http://127.0.0.1:1234/group/'
        self.urlmsgtime = 'http://127.0.0.1:1234/timemsg/'
        
    def groupLists_post(self):
        data = { 'addName':u'刘宏伟',
                'delName':'',
                'srcRnm':u'asd',
                'dstRnm':u'asdf',
                'srcCpy':u'qwe',
                'dstCpy':u'asdf',
            }
        r = requests.post(url = self.urlgrouplists, data = json.dumps(data))
        print r.text
        
    def groupLists_get(self):
        json_data = requests.get(self.urlgrouplists)
        #data = json.loads(json_data)
        #json_data.text = json_data.text.encode('utf-8')
        print json_data.text
        data = json.loads(json_data.text)
        print (data)
        
        
        #pprint.pprint(json_data.text)
    
    def group_get(self):
        url = self.urlgroup
        param = {
            u'groupName':u'刘宏伟',
            }
        data = requests.get(url=url,params=param)
        if data.text != None:   
            data = json.loads(data.text)
            print (data)
        else:
            print None
    
    def group_post(self):
        url = self.urlgroup
        data = {
            u'groupName':u'刘宏伟',
            u'delName':[u'刘宏伟'],
            u'addName':[u'罗军'],
            } 
        data = requests.post(url=url, data = json.dumps(data))
        print (data.text)
        
    def test_get(self):
        params = {u'name':u'刘宏伟',
                  u'arg3':u'中文'}
        data = requests.get(url=self.urltest,params=params)
        print 'client',
        print type(data.text)
        print 'client',
        print data.text
    
    def test_post(self):
        data = {
            u'name':u'刘宏伟',
            u'grade':u'99'}
        data = requests.post(url=self.urltest,data=json.dumps(data))
        print 'client',
        print type(data.text)
        print 'client',
        print data.text
    
    def msg_time(self):
        data = {
            u'msgName':u'罗军',
            u'msgTime':u'0,23',
            u'msgWord':u'是不是23'
            }
        data = requests.post(url=self.urlmsgtime,data=json.dumps(data))
        datas = json.loads(data.text)
        for data in datas:
            print data  
        
if __name__ == '__main__':
    
    client = ClientTest()
    #client.groupLists_get()
    client.groupLists_get()
    client.msg_time()
    
    #client.group_post()
    #client.test_post()