import requests
import json
import pymongo

# 读取cookie信息
with open('cookie_dict.txt', 'r') as f:
    cookie_dict=json.load(f)

# 连接mongodb数据库
client = pymongo.MongoClient(host='127.0.0.1', port=27017)
db = client['test']
v = db.video

# 选择视频分区爬取信息
headers = {'header':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'}
for page in range(20):
    url = 'https://api.bilibili.com/x/web-interface/newlist?rid=28&type=0&pn={}&ps=20&jsonp=jsonp&_=1543730016233'.format(page)
    res = requests.get(url, headers=headers, cookies=cookie_dict)
    archives = json.loads(res.text)['data']['archives']
    for archive in archives:
        result = v.insert(archive)
