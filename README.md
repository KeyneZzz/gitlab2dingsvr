# gitlab钉钉通知服务

## 简介

如果你的开发团队使用gitlab作为托管仓库、开发周期管理和持续集成工具，那么肯定会希望gitlab的事件（例如issue回复、mergerequest评论、pipeline状态等）能够及时通知到相关成员，gitlab虽然有相关的提醒，但是基本遵照老外的工作惯例，使用邮件进行通知
如果你的团队同时使用钉钉作为日常的IM工具的话，本项目可以帮助你将gitlab事件通知到相关人员的钉钉上

项目使用了gitlab的webhook，gitlab将事件消息发送到本服务上，再由本服务调用钉钉开放接口将消息发送到指定个人

## 文件结构

* gitlab2ding:shell快捷命令，启停和重启，需要添加执行权限
* gitlab2dingsvr.py:服务主程序，接受webhook并转为钉钉消息发送，接收并处理账号绑定
* labFetchUser.py:获取全体成员钉钉uid，需要手动运行

## 配置

### config.ini 文件【必须】

		[config]
		debug = 0
		debuger = 0123456789
		agentid = 0123456789
		port = 30000
		corpid = 0123456789
		corpsecret = 12345qwerty
		gitlabtoken = 12345qwerty
		gitlaburl = http://gitlab.yours.com
		webhookurl = http://gitlab.yours.com/gitlab2dingsvr

-----------
	* debug :
		* 0 :normal
		* 1 :send to user and debuger
		* 2 :send to debuger only
	* debuger:debuger的dinguid
	* agentid:注册钉钉企业应用时提供的应用id
	* port:服务监听的端口，设置在gitlab服务器上的话需要更改gitlab的nginx配置进行定向
	* corpid和corpsecret:钉钉为企业应用开发提供的企业信息查询token，在向钉钉请求和发送数据时使用
	* gitlabtoken:使用gitlab api时所需要的token
	* gitlaburl:gitlab服务器url，不要带最后的斜杠，如`http://gitlab.yours.com`
	* webhookurl:运行本通知服务的地址，同样不要带最后的斜杠，如`http://gitlab.yours.com/gitlab2dingsvr`
	* 以上字段均不需要使用引号包围

### gitlab配置
	
例如，gitlab服务器的url为`http://gitlab.yours.com`，并且希望把本服务配置在`http://gitlab.yours.com/gitlab2dingsvr`，则需要在gitlab服务器上找到`/etc/gitlab/gitlab.rb`文件，并添加如下配置

`nginx['custom_gitlab_server_config'] = "location /gitlab2dingsvr {\n proxy_cache off; \nproxy_pass http://127.0.0.1:30000;\n}\n"`

其中端口号30000可以自定义，但是需要与上文config中port项配置的端口号相同。修改该配置文件后需要运行`sudo gitlab-ctl reconfigure`使配置生效

## 运行

1. 配置config.ini和gitlab.rb
2. gitlab2ding添加运行权限
3. 运行一次labFetchUser.py:`python3 labFetchUser.py`
4. 启动服务:`./gitlab2ding start`

## 使用

### 1.关联钉钉账号
复制下方链接，并根据自己实际情况修改相应字段：
* mobile： 必须。你的钉钉注册手机号。
* username： 必须。你在Gitlab上的**Username（点开右上角头像后第二行@开头的字段，也是你登录时所用的用户名，此项务必检查无误）**
* email： 可选。你在git提交中使用的email（如果你不是代码开发者，则不需要提交这一项)

`http://gitlab.yours.com/gitlab2dingsvr?action=linkuser&mobile=13012341234&username=user`

`http://gitlab.yours.com/gitlab2dingsvr?action=linkuser&mobile=13012341234&username=user&email=user@mail.com`

改好以后复制到浏览器地址栏中直接访问，获得如下结果则关联成功。

```
User found.
Git email added.
Gitlab username added.
```

### 2.在project中添加webhook
  1. 请project负责人打开项目页面，在左侧导航栏中打开Settings - Integrations 
  2. 在打开的设置页面中，在第一行的URL添加地址：`http://gitlab.yours.com/gitlab2dingsvr`然后在下方的Trigger选择区域勾选所有消息类型。
  3. 完成后在下方点击Add Webhook即可。

## 备注

* 一些和钉钉交互的功能详情，可以查阅[钉钉开放平台的api文档](https://open-doc.dingtalk.com/docs/doc.htm?spm=a219a.7629140.0.0.AFXfTL&treeId=367&articleId=107549&docType=1)