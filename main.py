from WEIBO.WEIBO import WEIBO
from WEIBO.Find import Find

if __name__ == '__main__':
    # 只要是一个能登陆的微博账号就行
    w = WEIBO()
    w.login()
    # 要查询的微博ID
    w.WBID = "WBID"
    #查询WBID所有粉丝及粉丝的粉丝/关注，所有关注及关注的关注/粉丝
    w.discoverRelation(max_fans=1000)

    #搜索潜在的可能认识的人
    F=Find("WBID")
    F.getRelation()
    F.sortSomeOne()