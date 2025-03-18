from urllib.parse import quote
UnStatuHeader = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "connection": "keep-alive",
    "dnt": "1",
    "host": "study.jxgbwlxy.gov.cn",
    "referer": "https://study.jxgbwlxy.gov.cn/index",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
    "x-hostname-header": "study.jxgbwlxy.gov.cn"
}
def LogginStatusHeader(cookie,refer=None):
    wlxytk = cookie['token']
    rt = cookie['rt']
    accountId = cookie['accountId']
    studentId = cookie['studentId']
    studentName = quote(cookie['studentName'])
    cookie_str = f"wlxytk={wlxytk};rt={rt};accountId={accountId};studentId={studentId};studentName={studentName};headImg=undefined"
    result = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": wlxytk,
        "connection": "keep-alive",
        "cookie": cookie_str,
        "host": "study.jxgbwlxy.gov.cn",
        "origin": "https://study.jxgbwlxy.gov.cn",
        "refreshauthorization": rt,
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
        "x-hostname-header": "study.jxgbwlxy.gov.cn"
    }
    if refer:
        result["referer"] = refer
    return result
