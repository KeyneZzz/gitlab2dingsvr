from http.server import BaseHTTPRequestHandler, HTTPServer
from os import path
from urllib.parse import urlparse
import urllib 
from urllib import request,parse
from time import localtime, strftime
import json,configparser
import sqlite3


config = configparser.ConfigParser()
config.read("config.ini")
corpid = config["config"]["corpid"]
corpsecret = config["config"]["corpsecret"]

req_dingapi = request.Request("https://oapi.dingtalk.com/gettoken?corpid="+corpid+"&corpsecret="+corpsecret)
data_from_dingapi = request.urlopen(req_dingapi).read()
data_for_access_token = json.loads(data_from_dingapi.decode("utf-8"))
access_token = data_for_access_token['access_token']

url = "https://oapi.dingtalk.com/department/list?access_token="+access_token
req_dingapi = request.Request(url)
data_from_dingapi = request.urlopen(req_dingapi).read()
data_departments = json.loads(data_from_dingapi.decode("utf-8"))
data_departments_list = data_departments["department"]

sqconn = sqlite3.connect('gitlab2ding.db')
sqc = sqconn.cursor()


name_list = {}
for department in data_departments_list:
	req_dingapi = request.Request("https://oapi.dingtalk.com/user/list?access_token="+access_token+"&department_id="+str(department["id"]))
	data_from_dingapi = request.urlopen(req_dingapi).read().decode("utf-8")
	data = json.loads(data_from_dingapi)
	data_userlist = data["userlist"]
	for user in data_userlist:
		if not user["name"] in name_list:
			sq_add_str="INSERT OR IGNORE INTO USERS (PHONE,NAME,DINGUID) VALUES ('"+user["mobile"]+"', '"+user["name"]+"', '"+user["userid"]+"')"
			sqc.execute(sq_add_str);
		name_list[user["name"]] = "added"

sqconn.commit()
sqconn.close()
