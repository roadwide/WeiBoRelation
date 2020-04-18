import os


class Find:

    def __init__(self, WBID):
        self.WBID = WBID
        self.relation = []
        self.path = "./data/"

    # 获取文本文件中的nickname和uid
    def openData(self, filename):
        ans = []
        with open(self.path + filename, encoding="utf-8") as f:
            for line in f.readlines():
                if line in ['\n', '\r\n']:
                    continue
                # 9:-1会将最后一位省略
                nickname = line.split("\t")[0][9:]
                # 此处-1将最后的换行省略
                uid = line.split("\t")[3][4:-1]
                ans.append((nickname, uid))
        return ans

    # 获取所有关注/粉丝的uid，返回uid list
    def getRelation(self):
        fans_data = self.openData(self.WBID + "_fans.txt")
        self.relation = fans_data[:]

        follow_data = self.openData(self.WBID + "_followed.txt")
        # 防止重复
        for i in follow_data:
            if i not in self.relation:
                self.relation.append(i)

    # 对relation的关注/粉丝进行统计，出现次数高证明可能认识
    def findSomeOne(self):
        SomeOne = {}
        for name, uid in self.relation:
            if os.path.isfile(self.path + uid + "_fans.txt") != True:
                print("不存在{}的粉丝数据".format(uid))
                fans_data = []
            else:
                fans_data = self.openData(uid + "_fans.txt")

            if os.path.isfile(self.path + uid + "_followed.txt") != True:
                print("不存在{}的关注数据".format(uid))
                follow_data = []
            else:
                follow_data = self.openData(uid + "_followed.txt")

            # 不去重，因为互相关注证明更亲密
            fansandfollow = fans_data + follow_data

            for n, u in fansandfollow:
                # 跳过自己
                if u == self.WBID:
                    continue
                # 已经有关系的跳过
                if (n, u) in self.relation:
                    continue

                if u in SomeOne.keys():
                    SomeOne[u]['count'] += 1
                else:
                    SomeOne[u] = {'name': n, 'count': 1}

        return SomeOne

    # 将findSomeOne的结果排序
    def sortSomeOne(self):
        someone = self.findSomeOne()
        # 默认是升序，reverse=True变为降序
        sortByCount = sorted(someone.items(), key=lambda i: i[1]['count'], reverse=True)
        for i in sortByCount:
            with open("findSomeOne.txt", "a+", encoding="utf-8") as f:
                print(i)
                print(i, file=f)
