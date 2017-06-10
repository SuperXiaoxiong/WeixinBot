#coding:utf-8
'''
Created on Jun 1, 2017

@author: ustc
'''
import psutil
from time import sleep
import requests
import json


url = 'http://127.0.0.1:8080/api_monitor'
wxkey = 'lgjiimd8p0tSuF7o5bXZHubH4'

level = [1]
machine_num = 1

i=0
cpu_state ={
    "cpu_percent_sum" : 0,
    "cpu_user_sum":0,
    "cpu_nice_sum":0,
    "cpu_system_sum":0,
    "cpu_idle_sum":0,
    "cpu_iowait_sum":0,
    "cpu_irq_sum":0,
    "cpu_softirq_sum":0,
    "cpu_steal_sum":0,
}
mem_state={
    "mem_total":0,
    "mem_used":0,
    "mem_free":0,
    "mem_percent":0,
}
proc_state = {
    "proc1":{"name":'',"mem":0,"cpu":0},
    "proc2":{"name":'',"mem":0,"cpu":0},
    "proc3":{"name":'',"mem":0,"cpu":0},
    "proc4":{"name":'',"mem":0,"cpu":0},
    "proc5":{"name":'',"mem":0,"cpu":0},
}
while i<66:
    print i
    print(" CPU: " + str(psutil.cpu_percent(1)) + "%")
    print(" mem: " + str(psutil.virtual_memory().percent) + "%")
    
    cpu_state["cpu_percent_sum"] += psutil.cpu_percent(1)              #cpu占用比
    cpu_state["cpu_user_sum"] += psutil.cpu_times().user              #用户态使用的cpu时间比
    cpu_state["cpu_nice_sum"] += psutil.cpu_times().nice              #用做nice加权的进程分配的用户态cpu时间比
    cpu_state["cpu_system_sum"] += psutil.cpu_times().system          #系统态使用的cpu时间比
    cpu_state["cpu_idle_sum"] += psutil.cpu_times().idle              #空闲的cpu时间比
    cpu_state["cpu_iowait_sum"] += psutil.cpu_times().iowait          #cpu等待磁盘写入完成时间
    cpu_state["cpu_irq_sum"] += psutil.cpu_times().irq                #硬中断消耗时间
    cpu_state["cpu_softirq_sum"] += psutil.cpu_times().softirq        #软中断消耗时间
    cpu_state["cpu_steal_sum"] += psutil.cpu_times().steal            #虚拟机偷取时间
    
    mem_state["mem_total"] += psutil.virtual_memory().total/1024/1024
    mem_state["mem_used"] += psutil.virtual_memory().used/1024/1024
    mem_state["mem_free"] += psutil.virtual_memory().free/1024/1024
    mem_state["mem_percent"] += psutil.virtual_memory().percent
    
    i = i + 10
    if i >= 60:
        
        pids = psutil.pids()
        process = []
        for pid in pids:
            process.append(psutil.Process(pid))
        top_process = sorted(process,key=lambda proc:proc.memory_percent(),reverse = True)
        
        print top_process[0].cpu_percent()
        for i in range(1,6):
            proc_name = "proc" + str(i)
            proc_state[proc_name]={"name":top_process[i-1].name(),"mem":top_process[i-1].memory_percent(),"cpu":top_process[i-1].cpu_percent()}
        
        for x in cpu_state:
            cpu_state[x] /=6
        for x in mem_state:
            mem_state[x] /=6
        response = requests.post(url,data={'machine_num':machine_num,'wxkey':wxkey,'level':level,'cpu_state':json.dumps(cpu_state),'mem_state':json.dumps(mem_state),"proc_state":json.dumps(proc_state)})
        print cpu_state
        i=0
        for x in cpu_state:
            cpu_state[x]=0
        for x in mem_state:
            mem_state[x] =0
        
    sleep(10)