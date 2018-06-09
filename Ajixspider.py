'''用ajax动态抓取头条街拍的图片
第一步，先抓取索引页，解析出json格式的url
第二步，抓取具体页，提取出照片的url
第三步，连接到mongDB建立数据库,下载到本地文件

配置信息在congfig中。
'''


from  urllib.parse import urlencode
import requests
import json
from  requests.exceptions import  RequestException
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient
from  config import *
from hashlib import md5
import os
from multiprocessing import Pool
client =MongoClient(MONGD_URL, connect=False)
db = client[MONGD_TABLE]


def get_page_index(offset,keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': 20,
        'cur_tab': 3
    }
    url = 'https://www.toutiao.com/search_content/?' + urlencode(data)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求索引页错误！',url)
        return None

def parse_page_index(html):
    data = json.loads(html)
    if data and  'data' in data.keys():
        for item in data.get('data'):
            yield item.get('article_url')

def download_image(url):
    print('正在下载。。。。',url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except RequestException:
        print("请求图片出错",url)
        return None

def save_image(content):
    file_path ='{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close()



def get_page_detail(url):
    try:
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'}
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求详情页错误！',url)
        return None

def parse_page_detail(html,url):
    soup = BeautifulSoup(html,'lxml')
    title = soup.select('title')[0].get_text()
    print(title)
    image_pattern = re.compile(' gallery: JSON.parse\("(.*?)"\)',re.S)
    result =re.search(image_pattern,html)
    if result:
        #print(result.group(1).replace("\\",""))

        data = json.loads(result.group(1).replace("\\",""))
        if data and "sub_images" in data.keys():
            sub_images = data.get('sub_images')
            images = [item.get('url') for item in sub_images]
            for image in images:download_image(image)
            return {
                'title': title,
                'url': url,
                'images': images
            }

def save_to_mongo(result):
    if db[MONGD_TABLE].insert(result):
        print('存储到mongDB成功', result)
        return True
    return False

def main(offset):
    html = get_page_index(offset,KEYWORD)
    #print(html)
    for url in parse_page_index(html):
        #print(url)
        html = get_page_detail(url)
        if html:

            result = parse_page_detail(html,url)
            if result:
                save_to_mongo(result)


        #if  html:
            #parse_page_detail(html)


if __name__ == '__main__':

    groups = [x * 20 for x in (GROUP_START, GROUP_END+1)]
    pool = Pool()
    pool.map(main, groups)




