#coding:utf-8
'''
Created on 2016年10月7日
@author: knight110
'''

import requests
import json
import pprint

class ClientTest(object):
    
    def __init__(self):
        self.urltest = 'http://127.0.0.1:1234/test'
        self.urltext = 'http://127.0.0.1:1234/text/'
    
    def test_post(self):
        data = { 'name':u'刘宏伟',
                'word':u'是不是傻',
            }
        r = requests.post(url = self.urltext, data = json.dumps(data))
        print r.text
        
    def test_get(self):
        json_data = requests.get(self.urltext)
        #data = json.loads(json_data)
        '''
        data = json.loads(json_data)
        print data
        '''
        pprint.pprint(json_data.text)
        
if __name__ == '__main__':
    
    client = ClientTest()
    client.test_get()
    client.test_post()