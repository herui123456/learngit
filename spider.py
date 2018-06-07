import requests
from  requests.exceptions import RequestException
import json
import re
from  multiprocessing import Pool
#得到一页网页的文件
def get_one_page(url):
    try:
        headers={'user-agent':'User-Agent:Mozilla/5.0(Macintosh;U;IntelMacOSX10_6_8;en-us)AppleWebKit/534.50(KHTML,likeGecko)Version/5.1Safari/534.50'}
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return  response.text
        return None
    except RequestException:
        return None
	
#解析库解析网页类容
def parse_one_page(html):
    pattern = re.compile('<dd>.*?board-index.*?(\d+)</i>.*?data-src="(.*?)".*?name"><a'
                         +'.*?>(.*?)</a?.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
                         +'.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>',re.S)
    items = re.findall(pattern,html)
    for item in items:
        yield {
            'index':item[0],
            'image':item[1],
            'title':item[2],
            'actor':item[3].strip()[3:],
            'time':item[4].strip()[5:],
            'score':item[5]+item[6]
        }
		
#写入txt文本文件
def write_to_file(content):
    with open('result.txt','a',encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii= False)+'\n')
        f.close()

#抓取10页的内容
def main(offset):
    url = 'http://maoyan.com/board/4?offset=' + str(offset)
    html = get_one_page(url)
    for item in parse_one_page(html):
        print(item)
        write_to_file(item)

if __name__ == '__main__':
    #for i in range(10):
    #    main(i*10)
    pool = Pool()
    pool.map(main,[i*10 for i in range(10)])#用进程池的方法，能加快速度获取网页。