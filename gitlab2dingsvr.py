#!/usr/bin/env python
#--coding:utf-8--

from http.server import BaseHTTPRequestHandler, HTTPServer
from os import path
from urllib.parse import urlparse
import urllib 
from urllib import request,parse
from time import localtime, strftime
import json,configparser,sqlite3,os


config = configparser.ConfigParser()
config.read("config.ini")

#git_members : gitemail = dinguid
#lab_members : gitlabusername = dinguid

def log(log_str):
    timestamp = strftime("[%d/%b/%Y %H:%M:%S]", localtime())
    print(timestamp + log_str)


def read_list_from_db(list_type_str):
    sqconn = sqlite3.connect('gitlab2ding.db')
    sqc = sqconn.cursor()
    if list_type_str == "git_members":
        user_list_tuple = sqc.execute("SELECT GITEMAIL,DINGUID FROM USERS")
    elif list_type_str == "lab_members":
        user_list_tuple = sqc.execute("SELECT GITLABUSERNAME,DINGUID FROM USERS")
    elif list_type_str == "ding_user_list":
        user_list_tuple = sqc.execute("SELECT PHONE,DINGUID FROM USERS")
    db_list_dict = {}

    db_user = user_list_tuple.fetchone()
    while db_user!=None:
        if db_user[0]!=None:
            db_list_dict[db_user[0]] = db_user[1]
        db_user = user_list_tuple.fetchone()

    sqconn.close()
    log(list_type_str+" updated from sqlite db")
    return db_list_dict

try:
    os.system("python3 labFetchUser.py")
except:
    log("labFetchUser fail")
else:
    log("labFetchUser success")
git_members = read_list_from_db("git_members")
lab_members = read_list_from_db("lab_members")

AgentID = config["config"]["agentid"]
port = int(config["config"]["port"])
debug = config["config"]["debug"]
debuger = config["config"]["debuger"]
# debug 0 :normal
#       1 :send to user and debuger
#       2 :send to debuger only
corpid = config["config"]["corpid"]
corpsecret = config["config"]["corpsecret"]
gitlabtoken = config["config"]["gitlabtoken"]
gitlaburl = config["config"]["gitlaburl"]
webhookurl = config["config"]["webhookurl"]


def sqlite_linkuser_add(phone_str,value_str,key_str):
    sqconn = sqlite3.connect('gitlab2ding.db')
    sqc = sqconn.cursor()
    sqc.execute("SELECT PHONE FROM USERS")
    try:
        sqc.execute("UPDATE USERS set "+key_str+" = '"+value_str+"' where PHONE='"+phone_str+"'")    
    except :
        log( "sqlite_linkuser_add fail:"+phone_str+";"+value_str+";"+key_str)
        sqconn.commit()
        sqconn.close()
    else:
        log( "sqlite_linkuser_add success:"+phone_str+";"+value_str+";"+key_str)
        sqconn.commit()
        sqconn.close()

def labuid2username(uid_str):
    req_labid2username = request.Request(gitlaburl+"/api/v4/users/"+uid_str+"?private_token="+gitlabtoken)
    data_from_lab = request.urlopen(req_labid2username).read()
    data_for_username = json.loads(data_from_lab.decode("utf-8"))
    username = data_for_username["username"]
    return username

def receiverSort(receiver_str):
    if (receiver_str[0]=="|"):
        receiver_str = receiver_str[1:]
    if (debug == "1" ):
        log( "[debug]receiver_str:" + receiver_str)
        receiver_str = receiver_str+ "|" + debuger
    if (debug == "2" ):
        log( "[debug]receiver_str:" + receiver_str)
        receiver_str = debuger
    return receiver_str



class gitlab2dingsvr_RequestHandler(BaseHTTPRequestHandler):
    # GET

    def do_POST(self):  
        timestamp = strftime("[%d/%b/%Y %H:%M:%S]", localtime())
        querypath = urlparse(self.path)
        filepath, query = querypath.path, querypath.query
        data_b = self.rfile.read(int(self.headers['content-length']))
        self.send_response(200)
        self.send_header('Content-type',"None")
        self.end_headers()

        data_s = data_b.decode("utf-8")
        data_json = json.loads(data_s)
        receiver_dingUid = None
        send_valid=0;

        if "event_name" in data_json:
            '''
                            ■                                       
                            ■                                       
              ■■■   ■   ■ ■■■■■    ■■■                              
             ■  ■   ■   ■   ■     ■  ■■                             
                ■   ■   ■   ■     ■   ■                             
             ■■■■   ■   ■   ■     ■   ■                             
             ■  ■   ■  ■■   ■     ■  ■■                             
             ■■■■■  ■■■ ■    ■■■   ■■■                              
                                              
                           ■      ■                    ■            
                           ■      ■                    ■            
                           ■      ■                    ■            
            ■  ■ ■   ■■■   ■■■■   ■■■■    ■■■    ■■■   ■  ■         
            ■ ■■ ■  ■  ■■  ■  ■   ■■ ■■  ■  ■■  ■  ■■  ■ ■          
             ■■■ ■  ■■■■■  ■   ■  ■   ■  ■   ■  ■   ■  ■■■          
             ■■ ■■  ■      ■   ■  ■   ■  ■   ■  ■   ■  ■ ■■         
             ■■ ■   ■  ■■  ■  ■   ■   ■  ■  ■■  ■  ■■  ■  ■         
             ■  ■    ■■■   ■■■■   ■   ■   ■■■    ■■■   ■   ■                  
            '''
            if data_json['event_name']=="project_create":
                new_project_id_str = str(data_json["project_id"])
                log( "new project:"+data_json["path_with_namespace"]+"(id:"+new_project_id_str+"), adding webhook")
                addHook_json_str = (
                "{\"id\":"+new_project_id_str+",\"url\": \""+webhookurl+"\" ,"
                "\"push_events\" : 1 ,"
                "\"issues_events\" : 1 ,"
                "\"confidential_issues_events\" : 1, "
                "\"merge_requests_events\" : 1, "
                "\"tag_push_events\" : 1, "
                "\"note_events\" : 1, "
                "\"confidential_note_events\" : 1,"
                "\"job_events\" : 1, "
                "\"pipeline_events\" : 1, "
                "\"wiki_page_events\" : 1, "
                "\"enable_ssl_verification\" : 1 }"
                )

                addHook_json_str_b = addHook_json_str.encode('utf-8')
                url = gitlaburl+"/api/v4/projects/"+new_project_id_str+"/hooks"
                headersAddhook = {"Private-Token": gitlabtoken ,"Content-Type":"application/json"}
                req_addhook = request.Request(url, data=addHook_json_str_b,headers=headersAddhook, method="POST")
                data_from_addhook_req = request.urlopen(req_addhook).read()
                log( data_from_addhook_req.decode('utf_8'))

        elif "object_kind" in data_json:
            '''                                             
                                       ■                 
                     ■■                ■  ■■             
                     ■■                ■  ■■             
                                       ■                 
             ■ ■■■   ■  ■ ■■■    ■■■   ■  ■  ■ ■■■    ■■■  
             ■■  ■■  ■  ■■  ■■   ■  ■  ■  ■  ■■  ■■   ■  ■ 
             ■    ■  ■  ■    ■  ■   ■  ■  ■  ■    ■  ■   ■ 
             ■    ■  ■  ■    ■  ■■■■■  ■  ■  ■    ■  ■■■■■ 
             ■    ■  ■  ■    ■  ■      ■  ■  ■    ■  ■     
             ■■  ■   ■  ■■  ■   ■■  ■  ■  ■  ■    ■  ■■  ■ 
             ■ ■■■   ■  ■ ■■■    ■■■   ■  ■  ■    ■   ■■■  
             ■          ■                                
             ■          ■                                
             ■          ■                                
            pipeline object
            to: commit(according to commit email)
            '''

            if (data_json['object_kind'] == "pipeline"):
                send_valid = 1
                log( "pipeline trigger received")
                if data_json['commit']['author']['email'] in git_members:
                    receiver_dingUid = git_members[data_json['commit']['author']['email']]
                    log( "committer email:" + data_json['commit']['author']['email'] + " found")
                status = data_json['object_attributes']['status']
                commit_msg = data_json['commit']['message']
                object_id = str(data_json['object_attributes']['id'])
                log(data_json["project"]["web_url"]+"/pipelines/"+object_id)
                project_name = data_json['project']['name']
    
                if receiver_dingUid==None :
                    send_valid = 0
                else:
                    receiver_dingUid = receiverSort(receiver_dingUid)
                    msg2dingapi_json_str=(
                    "{\"touser\": \""+receiver_dingUid+"\", \"agentid\": \""+AgentID+"\","
                    "\"msgtype\": \"markdown\","
                    "\"markdown\": {\"title\": \"最近提交的CI状态变化\","
                    "\"text\": \"## 最近提交的CI状态变化为"+status+" \\n"
                    "### 项目："+project_name.replace("\"","\\\"")+" \\n"
                    "### 提交备注："+commit_msg.replace("\"","\\\"")+" \\n"
                    "[点击查看]("+data_json["project"]["web_url"]+"/pipelines/"+object_id+")"+timestamp+"\"} }"
                    )
                    msg2dingapi_b = msg2dingapi_json_str.encode('utf-8')
    
                '''
                 ■■                              
                 ■■                              
                                                 
                 ■   ■■    ■■   ■    ■   ■■■     
                 ■  ■  ■  ■  ■  ■    ■   ■  ■    
                 ■  ■     ■     ■    ■  ■   ■    
                 ■   ■■    ■■   ■    ■  ■■■■■    
                 ■     ■     ■  ■    ■  ■        
                 ■  ■  ■  ■  ■  ■■  ■■  ■■  ■    
                 ■   ■■    ■■    ■■■ ■   ■■■     
                issue object: create, at, edit
                msg to: author, at, assignee(according to lab username)
                '''
            elif (data_json['object_kind'] == "issue"):
                send_valid=1;
                log( "issue trigger received")
                if(data_json["user"]["username"] in lab_members):
                    receiver_dingUid = lab_members[data_json["user"]["username"]]#to author
                    log("author "+data_json["user"]["username"]+" get.")
                if("assignees" in data_json):
                    if("username" in data_json["assignees"][0]):
                        if(data_json["assignees"][0]["username"] in lab_members):
                            receiver_dingUid = receiver_dingUid + "|" + lab_members[data_json["assignees"][0]["username"]]#to assignee
                            log("assignee "+data_json["assignees"][0]["username"]+" get.")
                issue_url = data_json["object_attributes"]["url"]
                log(issue_url)
                issue_title = data_json["object_attributes"]["title"]
                issue_id = str(data_json["object_attributes"]["iid"])
                issue_content = data_json['object_attributes']['description']
                issue_content_dict = issue_content.split()
                for content in issue_content_dict:
                    if (content[0]=="@"):
                        for key in lab_members.keys():
                            if (content[1:]==key):
                                receiver_dingUid = receiver_dingUid+"|"+lab_members[key]#to at
                                log("at "+key+" get.")
                project_name = data_json['project']['name']
    
    
                if receiver_dingUid==None :
                    send_valid = 0
                else:
                    receiver_dingUid = receiverSort(receiver_dingUid)
                    msg2dingapi_json_str=(
                    "{\"touser\": \""+receiver_dingUid+"\", \"agentid\": \""+AgentID+"\","
                    "\"msgtype\": \"markdown\","
                    "\"markdown\": {\"title\": \"issue#"+issue_id+"通知\","
                    "\"text\": \"## 和你相关的issue#"+issue_id+"通知 \\n"
                    "### 项目："+project_name.replace("\"","\\\"")+" \\n"
                    "### 标题："+issue_title.replace("\"","\\\"")+" \\n"
                    "[点击查看]("+issue_url+")"+timestamp+"\"} }"
                    )
                    msg2dingapi_b = msg2dingapi_json_str.encode('utf-8')
            
                '''
                                                                                     
                     ■■       ■                              ■■■■■                   
                     ■■■     ■■                              ■   ■■                  
                     ■ ■     ■■                              ■    ■                  
                     ■ ■■   ■ ■    ■■■   ■ ■■   ■■ ■   ■■■   ■    ■   ■■■     ■■■■  
                     ■ ■■   ■ ■    ■  ■  ■■    ■  ■■   ■  ■  ■   ■    ■  ■   ■  ■■  
                     ■  ■   ■ ■   ■   ■  ■    ■    ■  ■   ■  ■■■■    ■   ■  ■    ■  
                     ■  ■■ ■  ■   ■■■■■  ■    ■    ■  ■■■■■  ■  ■    ■■■■■  ■    ■  
                     ■   ■■■  ■   ■      ■    ■    ■  ■      ■   ■   ■      ■    ■  
                     ■   ■■■  ■   ■■  ■  ■    ■■  ■■  ■■  ■  ■   ■■  ■■  ■  ■■  ■■  
                     ■    ■   ■    ■■■   ■     ■■■ ■   ■■■   ■    ■■  ■■■    ■■■ ■  
                                                   ■                             ■  
                                               ■  ■                              ■  
                                                ■■■                              ■   
                                                                                     
                merge request object: create, at, edit
                msg to: author, at, assignee(according to lab username)
                '''
            elif (data_json['object_kind'] == "merge_request"):
                send_valid=1;
                log( data_json['object_kind']+" trigger received")
                author_labusername = labuid2username(str(data_json["object_attributes"]["author_id"]))
                if(author_labusername in lab_members):
                    receiver_dingUid = lab_members[author_labusername]#to author
                    log("author "+author_labusername+" get.")
                if("assignee" in data_json):
                    if("username" in data_json["assignee"][0]):
                        if(data_json["assignee"][0]["username"] in lab_members):
                            receiver_dingUid = receiver_dingUid + "|" + lab_members[data_json["assignee"][0]["username"]]#to assignee
                            log("assignee "+data_json["assignee"][0]["username"]+" get.")
                object_url = data_json["object_attributes"]["url"]
                log(object_url)
                merge_req_title = data_json["object_attributes"]["title"]
                merge_req_id = str(data_json["object_attributes"]["iid"])
    
                merge_req_content = data_json['object_attributes']['description']
                merge_req_content_dict = merge_req_content.split()
                for content in merge_req_content_dict:
                    if (content[0]=="@"):
                        for key in lab_members.keys():
                            if (content[1:]==key):
                                receiver_dingUid = receiver_dingUid+"|"+lab_members[key]#to at
                                log("at "+key+" get.")
                project_name = data_json['project']['name']
    
    
                if receiver_dingUid==None :
                    send_valid = 0
                else:
                    receiver_dingUid = receiverSort(receiver_dingUid)
                    msg2dingapi_json_str=(
                    "{\"touser\": \""+receiver_dingUid+"\", \"agentid\": \""+AgentID+"\","
                    "\"msgtype\": \"markdown\","
                    "\"markdown\": {\"title\": \"MergeRequest#"+merge_req_id+"通知\","
                    "\"text\": \"## 和你相关的MergeRequest#"+merge_req_id+"通知 \\n"
                    "### 项目："+project_name.replace("\"","\\\"")+" \\n"
                    "### 标题："+merge_req_title.replace("\"","\\\"")+" \\n"
                    "[点击查看]("+object_url+")"+timestamp+"\"} }"
                    )
                    msg2dingapi_b = msg2dingapi_json_str.encode('utf-8')
            
                '''
                 ■■                                                                                                                  
                 ■■                                                                                           ■                      
                                                                                                              ■                      
                 ■   ■■    ■■   ■    ■   ■■■             ■■    ■■■■   ■ ■■  ■■■   ■ ■■  ■■■    ■■■   ■ ■■■   ■■■                     
                 ■  ■  ■  ■  ■  ■    ■   ■  ■           ■  ■   ■  ■■  ■■  ■■  ■■  ■■  ■■  ■■   ■  ■  ■■  ■■   ■                      
                 ■  ■     ■     ■    ■  ■   ■          ■      ■    ■  ■   ■    ■  ■   ■    ■  ■   ■  ■    ■   ■                      
                 ■   ■■    ■■   ■    ■  ■■■■■          ■      ■    ■  ■   ■    ■  ■   ■    ■  ■■■■■  ■    ■   ■                      
                 ■     ■     ■  ■    ■  ■              ■      ■    ■  ■   ■    ■  ■   ■    ■  ■      ■    ■   ■                      
                 ■  ■  ■  ■  ■  ■■  ■■  ■■  ■           ■  ■  ■■  ■   ■   ■    ■  ■   ■    ■  ■■  ■  ■    ■   ■                      
                 ■   ■■    ■■    ■■■ ■   ■■■             ■■    ■■■■   ■   ■    ■  ■   ■    ■   ■■■   ■    ■    ■                     
        
                issue comment object: new comment, at, edit
                msg to: comment author, at, issue author and assignee
                '''
            elif (data_json['object_kind'] == "note") and (data_json['object_attributes']['noteable_type'] == "Issue") :
                send_valid=1;
                log( data_json['object_attributes']['noteable_type'] +" comment trigger received")
                if(data_json["user"]["username"] in lab_members):
                    receiver_dingUid = lab_members[data_json["user"]["username"]]
                    log("comment author "+data_json["user"]["username"]+" get.")
    
                comment_url = data_json["object_attributes"]["url"]
                log(comment_url)
                comment_content = data_json['object_attributes']['note']
                content_dict = comment_content.split()
                for content in content_dict:
                    if (content[0]=="@"):
                        for key in lab_members.keys():
                            if (content[1:]==key):
                                receiver_dingUid = receiver_dingUid+"|"+lab_members[key]
                                log("at "+key+" get.")
    
                # content above are same in object kind NOTE (comment) 
    
                issue_author_id = str(data_json["issue"]["author_id"])
                issue_author = labuid2username(issue_author_id)
                if(issue_author in lab_members):
                    receiver_dingUid = receiver_dingUid+"|"+lab_members[issue_author]
                    log("issue author "+issue_author+" get.")
    
                if data_json["issue"]["assignee_id"] !=  None :
                    issue_assignee_id = str(data_json["issue"]["assignee_id"])
                    issue_assignee = labuid2username(issue_assignee_id)
                    if(issue_assignee in lab_members):
                        receiver_dingUid = receiver_dingUid+"|"+lab_members[issue_assignee]
                        log("issue assignee "+issue_assignee+" get.")
                issue_id = str(data_json["issue"]["iid"])
                issue_title = str(data_json["issue"]["title"])
    
                project_name = data_json['project']['name']
    
                if receiver_dingUid==None :
                    send_valid = 0
                else:
                    receiver_dingUid = receiverSort(receiver_dingUid)
                    msg2dingapi_json_str=(
                    "{\"touser\": \""+receiver_dingUid+"\", \"agentid\": \""+AgentID+"\","
                    "\"msgtype\": \"markdown\","
                    "\"markdown\": {\"title\": \"issue#"+issue_id+"评论通知\","
                    "\"text\": \"## 和你相关的issue#"+issue_id+"评论 \\n"
                    "### 项目："+project_name.replace("\"","\\\"")+" \\n"
                    "### 标题："+issue_title.replace("\"","\\\"")+" \\n"
                    "[点击查看]("+comment_url+")"+timestamp+"\"} }"
                    )
                    msg2dingapi_b = msg2dingapi_json_str.encode('utf-8')
                '''
                                                                                  
                                                        ■■                                                                                        
                                                        ■■  ■                                                                    ■                
                                                            ■                                                                    ■                
                   ■■    ■■■■   ■ ■■  ■■■   ■ ■■  ■■■   ■  ■■■■             ■■    ■■■■   ■ ■■  ■■■   ■ ■■  ■■■    ■■■   ■ ■■■   ■■■■              
                  ■  ■   ■  ■■  ■■  ■■  ■■  ■■  ■■  ■■  ■   ■              ■  ■   ■  ■■  ■■  ■■  ■■  ■■  ■■  ■■   ■  ■  ■■  ■■   ■                
                 ■      ■    ■  ■   ■    ■  ■   ■    ■  ■   ■             ■      ■    ■  ■   ■    ■  ■   ■    ■  ■   ■  ■    ■   ■                
                 ■      ■    ■  ■   ■    ■  ■   ■    ■  ■   ■             ■      ■    ■  ■   ■    ■  ■   ■    ■  ■■■■■  ■    ■   ■                
                 ■      ■    ■  ■   ■    ■  ■   ■    ■  ■   ■             ■      ■    ■  ■   ■    ■  ■   ■    ■  ■      ■    ■   ■                
                  ■  ■  ■■  ■   ■   ■    ■  ■   ■    ■  ■   ■              ■  ■  ■■  ■   ■   ■    ■  ■   ■    ■  ■■  ■  ■    ■   ■                
                   ■■    ■■■■   ■   ■    ■  ■   ■    ■  ■    ■■             ■■    ■■■■   ■   ■    ■  ■   ■    ■   ■■■   ■    ■    ■■              
                                                                                                                                              
                commit comment object: new comment, at, edit
                msg to: comment author, at, commit author
                '''
            elif (data_json['object_kind'] == "note") and (data_json['object_attributes']['noteable_type'] == "Commit") :
                send_valid=1;
                log( data_json['object_attributes']['noteable_type'] +" comment trigger received")
                if(data_json["user"]["username"] in lab_members):
                    receiver_dingUid = lab_members[data_json["user"]["username"]]
                    log("comment author "+data_json["user"]["username"]+" get.")
    
                comment_url = data_json["object_attributes"]["url"]
                log(comment_url)
                comment_content = data_json['object_attributes']['note']
                content_dict = comment_content.split()
                for content in content_dict:
                    if (content[0]=="@"):
                        for key in lab_members.keys():
                            if (content[1:]==key):
                                receiver_dingUid = receiver_dingUid+"|"+lab_members[key]
                                log("at "+key+" get.")
    
                # content above are same in object kind NOTE (comment) 
    
                commit_author_email = data_json["commit"]["author"]["email"]
                if(commit_author_email in git_members):
                    receiver_dingUid = receiver_dingUid+"|"+git_members[commit_author_email]
                    log("commit author "+commit_author_email+" get.")
    
                commit_msg = data_json['commit']['message']
                project_name = data_json['project']['name']
    
                if receiver_dingUid==None :
                    send_valid = 0
                else:
                    receiver_dingUid = receiverSort(receiver_dingUid)
                    msg2dingapi_json_str=(
                    "{\"touser\": \""+receiver_dingUid+"\", \"agentid\": \""+AgentID+"\","
                    "\"msgtype\": \"markdown\","
                    "\"markdown\": {\"title\": \"commit评论通知\","
                    "\"text\": \"## 和你相关的commit评论 \\n"
                    "### 项目："+project_name.replace("\"","\\\"")+" \\n"
                    "### 提交备注："+commit_msg.replace("\"","\\\"")+" \\n"
                    "[点击查看]("+comment_url+")"+timestamp+"\"} }"
                    )
                    msg2dingapi_b = msg2dingapi_json_str.encode('utf-8')
    
                '''
                                                                                         
                                                                                         
                     ■■       ■                              ■■■■■                                   
                     ■■■     ■■                              ■   ■■                                  
                     ■ ■     ■■                              ■    ■                                  
                     ■ ■■   ■ ■    ■■■   ■ ■■   ■■ ■   ■■■   ■    ■   ■■■     ■■■■  
                     ■ ■■   ■ ■    ■  ■  ■■    ■  ■■   ■  ■  ■   ■    ■  ■   ■  ■■  
                     ■  ■   ■ ■   ■   ■  ■    ■    ■  ■   ■  ■■■■    ■   ■  ■    ■  
                     ■  ■■ ■  ■   ■■■■■  ■    ■    ■  ■■■■■  ■  ■    ■■■■■  ■    ■  
                     ■   ■■■  ■   ■      ■    ■    ■  ■      ■   ■   ■      ■    ■  
                     ■   ■■■  ■   ■■  ■  ■    ■■  ■■  ■■  ■  ■   ■■  ■■  ■  ■■  ■■  
                     ■    ■   ■    ■■■   ■     ■■■ ■   ■■■   ■    ■■  ■■■    ■■■ ■  
                                                   ■                             ■  
                                               ■  ■                              ■  
                                                ■■■                              ■                                                           
                                                                                              
                                                                             ■                
                                                                             ■                
                        ■■    ■■■■   ■ ■■  ■■■   ■ ■■  ■■■    ■■■   ■ ■■■   ■■■■              
                       ■  ■   ■  ■■  ■■  ■■  ■■  ■■  ■■  ■■   ■  ■  ■■  ■■   ■                
                      ■      ■    ■  ■   ■    ■  ■   ■    ■  ■   ■  ■    ■   ■                
                      ■      ■    ■  ■   ■    ■  ■   ■    ■  ■■■■■  ■    ■   ■                
                      ■      ■    ■  ■   ■    ■  ■   ■    ■  ■      ■    ■   ■                
                       ■  ■  ■■  ■   ■   ■    ■  ■   ■    ■  ■■  ■  ■    ■   ■                
                        ■■    ■■■■   ■   ■    ■  ■   ■    ■   ■■■   ■    ■    ■■              
                                                          
                merge request comment object: new comment, at, edit
                msg to: comment author, at, merge requester, merge assignee
                '''
            elif (data_json['object_kind'] == "note") and (data_json['object_attributes']['noteable_type'] == "MergeRequest") :
                send_valid=1;
                log( data_json['object_attributes']['noteable_type'] +" comment trigger received")
                author_labusername = labuid2username(str(data_json["object_attributes"]["author_id"]))
                if(author_labusername in lab_members):
                    receiver_dingUid = lab_members[author_labusername]#to author
                    log("author "+author_labusername+" get.")
    
                comment_url = data_json["object_attributes"]["url"]
                log(comment_url)
                comment_content = data_json['object_attributes']['note']
                content_dict = comment_content.split()
                for content in content_dict:
                    if (content[0]=="@"):
                        for key in lab_members.keys():
                            if (content[1:]==key):
                                receiver_dingUid = receiver_dingUid+"|"+lab_members[key]
                                log("at "+key+" get.")
    
                # content above are same in object kind NOTE (comment) 
    
                req_author_id = str(data_json["merge_request"]["author_id"])
                req_author = labuid2username(req_author_id)
                if(req_author in lab_members):
                    receiver_dingUid = receiver_dingUid+"|"+lab_members[req_author]
                    log("MergeRequest author "+req_author+" get.")
    
                if data_json["merge_request"]["assignee_id"] !=  None :
                    req_assignee_id = str(data_json["merge_request"]["assignee_id"])
                    req_assignee = labuid2username(req_assignee_id)
                    if(req_assignee in lab_members):
                        receiver_dingUid = receiver_dingUid+"|"+lab_members[req_assignee]
                        log("MergeRequest assignee "+req_assignee+" get.")
    
                merge_req_title = data_json['merge_request']['title']
                project_name = data_json['project']['name']
    
                if receiver_dingUid==None :
                    send_valid = 0
                else:
                    receiver_dingUid = receiverSort(receiver_dingUid)
                    msg2dingapi_json_str=(
                    "{\"touser\": \""+receiver_dingUid+"\", \"agentid\": \""+AgentID+"\","
                    "\"msgtype\": \"markdown\","
                    "\"markdown\": {\"title\": \"MergeRequest通知\","
                    "\"text\": \"## 和你相关的MergeRequest评论 \\n"
                    "### 项目："+project_name.replace("\"","\\\"")+" \\n"
                    "### 标题："+merge_req_title.replace("\"","\\\"")+" \\n"
                    "[点击查看]("+comment_url+")"+timestamp+"\"} }"
                    )
                    msg2dingapi_b = msg2dingapi_json_str.encode('utf-8')
    
                '''
                                           ■                                  
                                           ■                                  
                                           ■                                  
                                           ■                                  
                  ■■    ■■■   ■ ■■■     ■■ ■      ■ ■■  ■■■    ■■     ■■ ■    
                 ■  ■   ■  ■  ■■  ■■   ■  ■■      ■■  ■■  ■■  ■  ■   ■  ■■    
                 ■     ■   ■  ■    ■  ■    ■      ■   ■    ■  ■     ■    ■    
                  ■■   ■■■■■  ■    ■  ■    ■      ■   ■    ■   ■■   ■    ■    
                    ■  ■      ■    ■  ■    ■      ■   ■    ■     ■  ■    ■    
                 ■  ■  ■■  ■  ■    ■  ■■  ■■      ■   ■    ■  ■  ■  ■■  ■■    
                  ■■    ■■■   ■    ■   ■■■ ■      ■   ■    ■   ■■    ■■■ ■    
                                                                         ■    
                                                                     ■  ■     
                                                                      ■■■   
                recognized object, have msg to send
                '''
            if (send_valid == 1):
                send_valid =0;
                req_dingapi = request.Request("https://oapi.dingtalk.com/gettoken?corpid="+corpid+"&corpsecret="+corpsecret)
                data_from_dingapi = request.urlopen(req_dingapi).read()
                data_for_access_token = json.loads(data_from_dingapi.decode("utf-8"))
                access_token = data_for_access_token['access_token']
                if(debug!="0"):
                    log( "[debug]access_token:" + access_token)
                url = "https://oapi.dingtalk.com/message/send?access_token="+access_token
                headers2dingapi={"Content-Type":"application/json"}
                req_dingapi = request.Request(url, data=msg2dingapi_b,headers=headers2dingapi, method="POST")
                data_from_dingapi = request.urlopen(req_dingapi).read()
                log( data_from_dingapi.decode('utf_8'))
                json_from_dingapi = json.loads(data_from_dingapi.decode("utf-8"))
                if (json_from_dingapi["errcode"]!=0):
                    print(msg2dingapi_json_str)
            else:   # send_valid==0, unhandled object kind
                log( "Object "+data_json['object_kind'] +" received. not handled")
                if (data_json['object_kind']=="note"):
                    log( "noteable_type "+data_json['object_attributes']['noteable_type'])
                if "object_attributes" in data_json:
                    if "url" in data_json['object_attributes']:
                        log( data_json['object_attributes']['url'])


        '''
        bind dingUid to git email and lab username
        query: action=&name=&username=&email=
        '''
    def do_GET(self):  
        method_get_req_dict = {}
        global git_members
        global lab_members
        querypath = urlparse(self.path)
        filepath, query = querypath.path, querypath.query
        response_text=""
        try:
            datas = urllib.parse.unquote(querypath.query).split("&")
            for data in datas:
                key = data.split("=")[0]
                value = data.split("=")[1]
                method_get_req_dict[key] = value
        except:
            self.send_response(400)
            self.send_header('Content-type',"text; charset=utf-8")
            self.end_headers()
            self.wfile.write("400 - Bad Request".encode("utf-8"))
            log("bad request: "+ querypath.query)
        else:
            self.send_response(200)
            self.send_header('Content-type',"text; charset=utf-8")
            self.end_headers()

            if "action" in method_get_req_dict:
    
                '''
                 ■             ■                                  
                 ■  ■■         ■                                  
                 ■  ■■         ■                                  
                 ■             ■                                  
                 ■  ■  ■ ■■■   ■   ■  ■    ■   ■■    ■■■   ■ ■■   
                 ■  ■  ■■  ■■  ■  ■   ■    ■  ■  ■   ■  ■  ■■     
                 ■  ■  ■    ■  ■ ■    ■    ■  ■     ■   ■  ■      
                 ■  ■  ■    ■  ■■■    ■    ■   ■■   ■■■■■  ■      
                 ■  ■  ■    ■  ■ ■    ■    ■     ■  ■      ■      
                 ■  ■  ■    ■  ■  ■   ■■  ■■  ■  ■  ■■  ■  ■      
                 ■  ■  ■    ■  ■   ■   ■■■ ■   ■■    ■■■   ■      
                                                      
                action: add new user link
                param: action, name(phone number,primary key), email(optional), username(gitlab username)
                '''
                if method_get_req_dict["action"] == "linkuser":                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
                    #ding_user_all = configparser.ConfigParser()
                    #ding_user_all.read("user_all")
                    #ding_user_list = ding_user_all["ding_userid_all"]
                    try:
                        os.system("python3 labFetchUser.py")
                    except:
                        log("labFetchUser fail")
                    else:
                        log("labFetchUser success")
                    ding_user_list = read_list_from_db("ding_user_list")
                    if method_get_req_dict["mobile"] in ding_user_list:
                        method_get_req_dict["dingUid"] = ding_user_list[method_get_req_dict["mobile"]]
                        response_text = "User found.\n"
                        if "email" in method_get_req_dict:
                            if method_get_req_dict["email"] not in git_members:
                                #config.set("gitmembers",method_get_req_dict["email"],method_get_req_dict["dingUid"])
                                #config.write(open('config.ini', 'w'))
                                sqlite_linkuser_add(method_get_req_dict["mobile"],method_get_req_dict["email"],"GITEMAIL")
                                response_text = response_text+"Git email added.\n"
                                log( "add git email for "+method_get_req_dict["mobile"] + ":"+method_get_req_dict["email"])
                            else:
                                response_text = response_text+"Git email already exists!!!\n"
                                log( "add git email for "+method_get_req_dict["mobile"] + ":"+method_get_req_dict["email"]+" fail:already exists")
                        if "username" in method_get_req_dict:
                            if method_get_req_dict["username"] not in lab_members:
                                #config.set("labmembers",method_get_req_dict["username"],method_get_req_dict["dingUid"])
                                #config.write(open('config.ini', 'w'))
                                sqlite_linkuser_add(method_get_req_dict["mobile"],method_get_req_dict["username"],"GITLABUSERNAME")
                                response_text = response_text+"Gitlab username added.\n"
                                log( "add lab username for "+method_get_req_dict["mobile"]+ ":"+method_get_req_dict["username"])
                            else:
                                response_text = response_text+"Gitlab username already exists!!!\n"
                                log( "add lab username for "+method_get_req_dict["mobile"]+ ":"+method_get_req_dict["username"]+" fail:already exists")
                        git_members = read_list_from_db("git_members")
                        lab_members = read_list_from_db("lab_members")
                    else:
                        response_text = "User not found.\n"
                        log( "cannot find user : "+method_get_req_dict["mobile"])
                else:
                    response_text = "error: action error"
                    log( "error: action error: "+method_get_req_dict["action"])
            else: # no action param in request
                response_text = "error: no action."
                log( "error: no action param.")
            self.wfile.write(response_text.encode("utf-8"))
def run():
    print('starting server, port', port)
    # Server settings
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, gitlab2dingsvr_RequestHandler)
    print('running server...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
