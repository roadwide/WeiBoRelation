#第一次详细了解package 从WEIBO这个包中导入WEIBO这个模块的WEIBO这个函数/类
from WEIBO.WEIBO import WEIBO

if __name__ == '__main__':
    # 只要是一个能登陆的微博账号就行
    w = WEIBO("username", "password")
    # 要查询的微博ID
    w.WBID = "WBID"
    w.login()
    w.get_all_follow()
    w.get_all_fans()
    w.get_recent_liked()
