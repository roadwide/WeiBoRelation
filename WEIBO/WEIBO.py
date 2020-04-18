import requests
import json
from bs4 import BeautifulSoup
import re
import time
import os


class WEIBO:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.s = requests.session()
        self.isLogin = False
        self.WBID = None
        self.T = 0
        self.path = "./data/"

        # 创建data文件夹
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def plusT(self):
        self.T += 3

    def minusT(self):
        if (self.T > 0):
            self.T -= 1

    # login
    def login(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36',
            'Referer': 'https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=https%3A%2F%2Fm.weibo.cn%2F',
        }
        self.s = requests.session()
        login_status = self.s.post("https://passport.weibo.cn/sso/login",
                                   data={
                                       "username": self.username,
                                       "password": self.password
                                   },
                                   headers=headers)
        login_req_json = json.loads(login_status.text)
        login_code = login_req_json['retcode']
        if (login_code == 20000000):
            print("login successfully")
            self.isLogin = True

    # request until success
    def getReq(self, url, errorinfo):
        while True:
            try:
                req = self.s.get(url)
                if req.status_code == 200:
                    self.minusT()
                    break
                else:
                    self.plusT()
                    print(errorinfo + " status_code error {}秒后重试".format(self.T))
                    time.sleep(self.T)
            except:
                self.plusT()
                print(errorinfo + " exception error {}秒后重试".format(self.T))
                time.sleep(self.T)
        return req

    # get how many pages followed
    # 有些用户的关注页是正常的，有些只有20页，原因不详
    # 这些用户在桌面端网页到第六页也会提示由于系统限制，你无法查看所有关注，如有疑问请点击
    def get_follow_pages(self):
        Pages = 0
        if (self.isLogin == False):
            print("not login")
        else:
            print("正在获取{}关注页数".format(self.WBID))
            url = "https://weibo.cn/" + self.WBID + "/follow"
            errorinfo = "获取关注页数时出现异常"
            req = self.getReq(url, errorinfo)
            html = req.text
            soup = BeautifulSoup(html, "html.parser")
            # 当关注的人数只有一页时没有跳转页的按钮，也就无法获取页数
            inputElem = soup.find(attrs={"name": "mp"})
            if (inputElem == None):
                Pages = 1
            else:
                Pages = eval(inputElem['value'])
        return Pages

    # get a page users's data
    def get_follow(self, page, max_fans=None):
        GroupUser = []
        if (self.isLogin == False):
            print("not login")
        else:
            print("{}正在获取第{}页关注".format(self.WBID, page))
            url = "https://weibo.cn/" + self.WBID + "/follow?page=" + str(page)
            errorinfo = "获取第{}页关注时出现异常".format(page)
            req = self.getReq(url, errorinfo)
            html = req.text
            soup = BeautifulSoup(html, "html.parser")
            table_list = soup.find_all("table")
            for i in table_list:
                # 起初用contents变成列表，但是发现有V认证的用户会多一个标签
                UserData = i.tr.find_all("td")[1]
                # 有意思，如果id里有粉丝两个字会出错
                FansCount = re.findall("<br\/>粉丝(.+?)人", str(UserData))[0]
                FansCount = eval(FansCount)
                # 直接从这里排除，减少后续请求获取uid
                if max_fans and FansCount > max_fans:
                    continue
                NickName = UserData.a.string
                URL = UserData.a["href"]
                errorinfo = "获取个人信息{}时出现异常".format(URL)
                profile_req = self.getReq(URL, errorinfo)
                profile_html = profile_req.text
                uid = re.findall("\/([0-9]+?)\/info", profile_html)[0]
                GroupUser.append((NickName, FansCount, URL, uid))
        return GroupUser

    # get all followed
    def get_all_follow(self, max_fans=None):
        if os.path.isfile(self.path + self.WBID + "_followed.txt"):
            print("{}关注数据已存在".format(self.WBID))
            return
        Pages = self.get_follow_pages()
        # range函数是前闭后开，所以要Pages+1
        # 那等于说之前都少获取一页数据
        for i in range(1, Pages + 1):
            GroupData = self.get_follow(i, max_fans=max_fans)
            for userdata in GroupData:
                nickname, fanscount, url, uid = userdata
                # 跳过粉丝数超过一定数的用户，在get_follow中实现，减少获取uid的请求
                # if max_fans and fanscount>max_fans:
                #     continue
                with open(self.path + self.WBID + "_followed.txt", "a+", encoding="utf-8") as f:
                    print(nickname)
                    print("nickname:{}\tfanscount:{}\turl:{}\tuid:{}".format(nickname, fanscount, url, uid), file=f)

    # get fans number
    def get_fans_num(self):
        html = self.s.get("https://weibo.cn/{}/profile".format(self.WBID)).text
        soup = BeautifulSoup(html, "html.parser")
        user_div = soup.find("div", class_="u")
        fans_num = re.findall(">粉丝\[(.+?)\]<", str(user_div))[0]
        return eval(fans_num)

    # get a page fans's data
    def get_fans(self, page):
        print("{}正在获取第{}页粉丝".format(self.WBID, page))
        user_url = "https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_" + self.WBID
        url = user_url + "&since_id=" + str(page)
        errorinfo = "获取第{}页粉丝时出现异常".format(page)

        req = self.getReq(url, errorinfo)
        txt = req.text

        fans_json = json.loads(txt)
        # 第一页要推送相关用户所以索引有两个，第二页开始不推送相关用户，只有一个索引
        # 有的会推送一类，有的推送两类，len(fans_data)等于2或3
        # 推送：这些大V用户关注了她、她的粉丝中你可能感兴趣的人、32个教育博主关注了他
        fans_data = fans_json['data']['cards']

        if (len(fans_data) == 0):
            print("没有更多粉丝")
            return 0
        # elif (len(fans_data) == 2):
        #     card_group = fans_data[1]['card_group']
        # 因为发现有的推送两个有的推送三个，所以直接取最后一个
        else:
            card_group = fans_data[-1]['card_group']
        # 由于微博反垃圾屏蔽一部分粉丝，所以真实粉丝会小于检测到的
        card_type = card_group[0]['card_type']
        if card_type != 10:
            print("没有更多粉丝")
            return 0
        UserData = []
        for i in card_group:
            user = i['user']
            nickname = user['screen_name']
            fans_count = user['followers_count']
            profile_url = user['profile_url']
            uid = re.findall("uid=([0-9]+?)&", profile_url)[0]
            UserData.append((nickname, fans_count, profile_url, uid))
        return UserData

    # get all fans
    def get_all_fans(self, max_fans=None):
        if os.path.isfile(self.path + self.WBID + "_fans.txt"):
            print("{}粉丝数据已存在".format(self.WBID))
            return
        max_turn = self.get_fans_num() // 20 + 1
        # 最多只能到250
        if (max_turn > 250):
            max_turn = 250
        # range函数前闭后开
        for i in range(1, max_turn + 1):
            GroupData = self.get_fans(i)
            # 等于0说明到头了
            if GroupData == 0:
                print("粉丝获取完毕")
                break
            for userdata in GroupData:
                nickname, fanscount, url, uid = userdata
                # 跳过粉丝数超过一定数的用户
                if max_fans and fanscount > max_fans:
                    continue
                with open(self.path + self.WBID + "_fans.txt", "a+", encoding="utf-8") as f:
                    print(nickname)
                    print("nickname:{}\tfanscount:{}\turl:{}\tuid:{}".format(nickname, fanscount, url, uid), file=f)

    # get recent liked weibo
    def get_recent_liked(self):
        # cookie公用，浏览器会通过js脚本进行跨域设置，而requests只读到了js脚本无法执行
        # 复制cookie并设置域名为.com,也就是桌面端页面
        # 翻了半天没找到重新设置cookie生效域的选项
        original_cookie = self.s.cookies.get_dict()
        newjar = requests.cookies.RequestsCookieJar()
        for (k, v) in original_cookie.items():
            newjar.set(k, v, domain="weibo.com")
        req = requests.get(
            "https://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100505&from=page_100505_profile&wvr=6&mod=like&pagebar=0&tab=like&current_page=&pl_name=Pl_Core_LikesFeedV6__68&id=100505{}&feed_type=1&page=1&pre_page=0".format(
                self.WBID),
            cookies=newjar)
        parse_txt = json.loads(req.text)
        html = parse_txt['data']
        soup = BeautifulSoup(html, "html.parser")
        url = soup.find(attrs={"node-type": "feed_list_item_date"})['href']
        print("最近点赞的微博 {}".format(url))
        return url

    # get someone's fans and follow
    def getRelationData(self, WBID, max_fans=None):
        # 获取所有粉丝和关注
        original_WBID = self.WBID
        self.WBID = WBID

        if max_fans:
            self.get_all_fans(max_fans=max_fans)
            self.get_all_follow(max_fans=max_fans)
        else:
            self.get_all_fans()
            self.get_all_follow()

        # 将WBID归位
        self.WBID = original_WBID

    # get someone's fans's fans and follow & follow's fans and follow
    def discoverRelation(self, max_fans=None):
        # 获取自身的粉丝和关注
        self.getRelationData(self.WBID, max_fans=max_fans)

        # 获取粉丝的粉丝和关注
        with open(self.path + self.WBID + "_fans.txt", encoding="utf-8") as f:
            for line in f.readlines():
                # 空行处理
                if line in ['\n', '\r\n']:
                    continue
                uid = line.split("\t")[3][4:-1]
                self.getRelationData(uid, max_fans=max_fans)

        # 获取关注的粉丝和关注
        with open(self.path + self.WBID + "_followed.txt", encoding="utf-8") as f:
            for line in f.readlines():
                if line in ['\n', '\r\n']:
                    continue
                uid = line.split("\t")[3][4:-1]
                self.getRelationData(uid, max_fans=max_fans)
