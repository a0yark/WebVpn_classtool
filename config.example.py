# 配置示例文件
# 请复制此文件为 config.py 并填入你的实际配置

# WebVPN 基础配置
WEBVPN_HOST = "webvpn.example.edu.cn"  # 你的 WebVPN 域名
CAS_PATH = "/cas/path/here"  # CAS 认证路径
JWGL_PATH = "/jwgl/path/here"  # 教务系统路径

# Cookie 配置
WENGINE_COOKIE_NAME = "wengine_vpn_ticket_xxx"  # Cookie 名称

# API 路径配置
API_PATHS = {
    "ticket": "/lyuapServer/v1/tickets/",
    "check_ticket": "/User/CheckTicketFromSSo",
    "get_courses": "/KcManage/GxKcManage/GetKcInfo/",
    "select_course": "/KcManage/GxKcManage/XkInfo/",
    "get_scores": "/SystemManage/CJManage/GetXsCjByXh/"
}
