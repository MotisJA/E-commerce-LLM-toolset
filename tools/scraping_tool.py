# 导入所需的库
import json
import requests
import time


# 定义爬取微博用户信息的函数
def scrape_weibo(url: str):
    """爬取相关鲜花服务商的资料"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
        "Referer": "https://weibo.com",
    }
    cookies = {"cookie": """SCF=AnUzeQzjh7AX_VDB0m8UjTIxbZHDKcZElXsQkamb6VuDdE7_gBQ_rsrVNv1n7bqBPTop3x-_w29nSgmz2tiCXfk.; XSRF-TOKEN=WkKt7llubQWrQtq-XY-Hdvum; PC_TOKEN=d2811fbe5c; SUB=_2A25Kb8tBDeRhGeFG61ER8yrOyDuIHXVpBUKJrDV8PUNbmtANLXeikW9NfpfsY0C4Oo0IZ_M-TlUCE0Ghwd5dsUYc; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFpbT4.rz6mTmB23r5.Pd8H5NHD95QN1h50eheXeoeNWs4DqcjCi--Ni-iWi-zRi--NiK.NiKnE; ALF=02_1737705489; WBPSESS=CEfLktBdsHSxronavg1XOKRJa_vcf3m6VUtKqLVHAAvzltnR4b_YpjivFbnOt8aoEAodacq0aINkW7URFCAboD3TmXF6GhVv7LtCXWwS7a_7tOTSoDn2VfXmB79ing5F97es_oVsNkNjxNQwuqEGYQ=="""}
    response = requests.get(url, headers=headers, cookies=cookies)
    time.sleep(3)  # 加上3s 的延时防止被反爬
    return response.text


# 根据UID构建URL爬取信息
def get_data(id):
    url = "https://weibo.com/ajax/profile/detail?uid={}".format(id)
    html = scrape_weibo(url)
    response = json.loads(html)

    return response
