import requests

# 目标 URL
# 注意：原始请求行中的 Path 和 Query String 拼接在一起
url = "https://webvpnnew.jxau.edu.cn/https/77726476706e69737468656265737421fae04690693a70516b468ca88d1b203b/KcManage/GxKcManage/GetKcInfo/8ceb6acb-c373-432a-b839-04f049f93d39?vpn-12-o2-jwgl.jxau.edu.cn"

# 请求头 Headers
headers = {
    "Host": "webvpnnew.jxau.edu.cn",
    "Connection": "keep-alive",
    "sec-ch-ua-platform": '"Windows"',
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    "sec-ch-ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "sec-ch-ua-mobile": "?0",
    "Accept": "*/*",
    "Origin": "https://webvpnnew.jxau.edu.cn",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
    # 注意：Cookie 可能包含会话信息，如果失效需要更新
    "Cookie": "show_vpn=0; show_fast=0; heartbeat=1; show_faq=0; wengine_vpn_ticketwebvpnnew_jxau_edu_cn=ebf8ba9f99ba873c; refresh=0"
}

# 请求体 Body
# 原始数据包内容: start=0&limit=20
data = {
    "start": "0",
    "limit": "20"
}

try:
    # 发送 POST 请求
    response = requests.post(url, headers=headers, data=data, verify=False) # verify=False 忽略 SSL 证书验证，视情况可选

    # 打印响应状态码
    print(f"Status Code: {response.status_code}")
    
    # 打印响应内容
    print("Response Body:")
    print(response.text)

except Exception as e:
    print(f"An error occurred: {e}")
