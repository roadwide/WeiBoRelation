from WEIBO import WEIBO

if (__name__ == '__main__'):
    w = WEIBO("username", "password")
    w.WBID = "WBID"
    w.login()
    w.get_all_follow()
    w.get_all_fans()
    w.get_recent_liked()
