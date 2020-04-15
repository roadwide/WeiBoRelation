import requests
import json
from bs4 import BeautifulSoup
import re
import time


class WEIBO:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.s = requests.session()
        self.isLogin = False
        self.WBID = None

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

    # get a page users's data
    def get_follow(self, page):
        GroupUser = []
        if (self.isLogin == False):
            print("not login")
        else:
            print("正在获取第{}页关注".format(page))
            html = self.s.get("https://weibo.cn/" + self.WBID + "/follow?page=" + str(page)).text
            soup = BeautifulSoup(html, "html.parser")
            table_list = soup.find_all("table")
            for i in table_list:
                # 起初用contents变成列表，但是发现有V认证的用户会多一个标签
                UserData = i.tr.find_all("td")[1]
                NickName = UserData.a.string
                # 有意思，如果id里有粉丝两个字会出错
                FansCount = re.findall("<br\/>粉丝(.+?)人", str(UserData))[0]
                URL = UserData.a["href"]
                GroupUser.append((NickName, eval(FansCount), URL))
        return GroupUser

    # get how many pages followed
    def get_follow_pages(self):
        Pages = 0
        if (self.isLogin == False):
            print("not login")
        else:
            print("正在获取关注页数")
            html = self.s.get("https://weibo.cn/" + self.WBID + "/follow").text
            soup = BeautifulSoup(html, "html.parser")
            Pages = soup.find(attrs={"name": "mp"})['value']
        return eval(Pages)

    # get all followed
    def get_all_follow(self):
        Pages = self.get_follow_pages()
        for i in range(1, Pages):
            GroupData = self.get_follow(i)
            for userdata in GroupData:
                nickname, fanscount, url = userdata
                with open("followed.txt", "a+", encoding="utf-8") as f:
                    print(nickname, fanscount, url)
                    print("nickname:{}\tfanscount:{}\turl:{}".format(nickname, fanscount, url), file=f)

    # get a page fans's data
    def get_fans(self, page):
        user_url = "https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_" + self.WBID
        while True:
            try:
                res = self.s.get(user_url + "&since_id=" + str(page))
                if (res.status_code == 200):
                    print("正在获取第{}页粉丝".format(page))
                    txt = res.text
                    break
                else:
                    print("访问异常，5分钟继续爬取")
                    time.sleep(300)
            except:
                print("出现异常，10秒后继续爬取")
                time.sleep(10)

        fans_json = json.loads(txt)
        # 第一页要推送相关用户所以索引有两个，第二页开始不推送相关用户，只有一个索引
        fans_data = fans_json['data']['cards']
        if (len(fans_data) == 0):
            card_group = False
        elif (len(fans_data) == 2):
            card_group = fans_data[1]['card_group']
        else:
            card_group = fans_data[0]['card_group']
        UserData = []
        for i in card_group:
            user = i['user']
            nickname = user['screen_name']
            fans_count = user['followers_count']
            profile_url = user['profile_url']
            UserData.append((nickname, fans_count, profile_url))
        return UserData

    # get fans number
    def get_fans_num(self):
        html = self.s.get("https://weibo.cn/{}/profile".format(self.WBID)).text
        soup = BeautifulSoup(html, "html.parser")
        user_div = soup.find("div", class_="u")
        fans_num = re.findall(">粉丝\[(.+?)\]<", str(user_div))[0]
        return eval(fans_num)

    # get all fans
    def get_all_fans(self):
        max_turn = self.get_fans_num() // 20 + 1
        # 最多只能到250
        if (max_turn > 250):
            max_turn = 250
        # range函数前闭后开
        for i in range(1, max_turn + 1):
            GroupData = self.get_fans(i)
            for userdata in GroupData:
                nickname, fanscount, url = userdata
                with open("fans.txt", "a+", encoding="utf-8") as f:
                    print(nickname, fanscount, url)
                    print("nickname:{}\tfanscount:{}\turl:{}".format(nickname, fanscount, url), file=f)

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
