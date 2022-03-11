import requests
import json
from bs4 import BeautifulSoup
import re
import time
import os


class WEIBO:
    def __init__(self):
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
        self.s = requests.session()

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

    # get a page users's data
    def get_follow(self, page):
        print("{}正在获取第{}页关注".format(self.WBID, page))
        user_url = "https://m.weibo.cn/api/container/getIndex?containerid=231051_-_followers_-_" + self.WBID
        url = user_url + "&page=" + str(page)
        errorinfo = "获取第{}页关注时出现异常".format(page)
        req = self.getReq(url, errorinfo)
        txt = req.text

        follows_json = json.loads(txt)
        # 第一页要推送相关用户所以索引有两个，第二页开始不推送相关用户，只有一个索引
        # 有的会推送一类，有的推送两类，len(fans_data)等于2或3
        # 推送：这些大V用户关注了她、她的粉丝中你可能感兴趣的人、32个教育博主关注了他
        follows_data = follows_json['data']['cards']

        if (len(follows_data) == 0):
            print("没有更多粉丝")
            return None
        # 因为发现有的推送两个有的推送三个，所以直接取最后一个
        else:
            card_group = follows_data[-1]['card_group']
        # 由于微博反垃圾屏蔽一部分粉丝，所以真实粉丝会小于检测到的
        card_type = card_group[0]['card_type']
        if card_type != 10:
            print("没有更多关注")
            return None
        UserData = []
        for i in card_group:
            user = i['user']
            if (user == None):
                continue
            nickname = user['screen_name']
            fans_count = user['followers_count']
            profile_url = user['profile_url']
            uid = re.findall("uid=([0-9]+?)&", profile_url)[0]
            UserData.append((nickname, fans_count, profile_url, uid))
        return UserData

    # get all followed
    def get_all_follow(self, max_fans=None):
        if os.path.isfile(self.path + self.WBID + "_followed.txt"):
            print("{}关注数据已存在".format(self.WBID))
            return
        Pages = self.get_follows_num() // 20 + 1
        # range函数是前闭后开，所以要Pages+1
        # 那等于说之前都少获取一页数据
        for i in range(1, Pages + 1):
            GroupData = self.get_follow(i)
            if (GroupData == None) :
                continue
            for userdata in GroupData:
                nickname, fanscount, url, uid = userdata
                # 跳过粉丝数超过一定数的用户，在get_follow中实现，减少获取uid的请求
                if (fanscount[-1] == '万' or fanscount[-1] == '亿'):
                    continue
                fanscount = eval(fanscount)
                if max_fans and fanscount>max_fans:
                    continue
                with open(self.path + self.WBID + "_followed.txt", "a+", encoding="utf-8") as f:
                    print(nickname)
                    print("nickname:{}\tfanscount:{}\turl:{}\tuid:{}".format(nickname, fanscount, url, uid), file=f)

    # 获得用户信息
    def getUserInfo(self):
        UserInfo = self.s.get("https://m.weibo.cn/profile/info?uid={}".format(self.WBID)).text
        UserInfo = json.loads(UserInfo)
        return UserInfo

    # get follows number
    def get_follows_num(self):
        UserInfo = self.getUserInfo()
        follows_num = UserInfo['data']['user']['follow_count']
        return follows_num

    # get fans number
    def get_fans_num(self):
        UserInfo = self.getUserInfo()
        fans_num = UserInfo['data']['user']['followers_count']
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
            if (user == None):
                continue
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
                if (fanscount[-1] == '万' or fanscount[-1] == '亿'):
                    continue
                fanscount = eval(fanscount)
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
