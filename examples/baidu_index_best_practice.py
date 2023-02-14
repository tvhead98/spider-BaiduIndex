"""
百度指数数据获取最佳实践
此脚本完成
1. 清洗关键词
2. 发更少请求获取更多的数据
3. 请求容错
4. 容错后并保留当前已经请求过的数据，并print已请求过的keywords
"""
from queue import Queue
from typing import Dict, List
import traceback
import time

import pandas as pd
from qdata.baidu_index import get_search_index
from qdata.baidu_index.common import check_keywords_exists, split_keywords

cookies = """BAIDUID=79DA73D9BD3058482FEA6E9BA8500748:FG=1; BAIDUID_BFESS=79DA73D9BD3058482FEA6E9BA8500748:FG=1; BDUSS=kRTRW1TV25oTkppV21ZR1hldH5vT3FkejNJMWZ2M0xmVndScFVRaTRkRjg1QkprRVFBQUFBJCQAAAAAAAAAAAEAAACHKYjodHZoZWFkOTgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHxX62N8V-tja; BDUSS_BFESS=kRTRW1TV25oTkppV21ZR1hldH5vT3FkejNJMWZ2M0xmVndScFVRaTRkRjg1QkprRVFBQUFBJCQAAAAAAAAAAAEAAACHKYjodHZoZWFkOTgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHxX62N8V-tja; BIDUPSID=79DA73D9BD3058482FEA6E9BA8500748; H_PS_PSSID=38185_36545_37559_38113_38055_38116_38150_37989_38177_38171_37925_38087_37900_26350_37957_22160_38008_37881; PSTM=1676367741; bdindexid=k8sds68t6nj210r3crrh2ue4u6; PTOKEN=51c84e16b63843dc4c8ecbbc7c210527; PTOKEN_BFESS=51c84e16b63843dc4c8ecbbc7c210527; STOKEN=6959a66990458dfb7d18cb9421d26510a5de4ea9b9d5a853ffac955faff65b06; STOKEN_BFESS=6959a66990458dfb7d18cb9421d26510a5de4ea9b9d5a853ffac955faff65b06; UBI=fi_PncwhpxZ%7ETaJcwLoNbVHVZVt3m0wZx2m; UBI_BFESS=fi_PncwhpxZ%7ETaJcwLoNbVHVZVt3m0wZx2m; BDSVRTM=8; BD_HOME=1; __yjs_st=2_MTE1YjNhZDg2ZmE3ZTcwMjQ4YWVkYWU1MGI1ZjVhYzdhNDY4NGY4OWU0ODAzYTliYzdkZjFjMWY4Y2E1MmM0MDc3MzMyZTY4MDY5NzAyMDM2YzhjMjE0MjA4NjEyOWU0YWM2NTk4MDExMDgxY2MxY2NhZTIzZDkxZjk3MDA0NGM5M2VmN2EyOGM4NzExNDcyYjE0OGEyYzQzODUxYTU2N2FkOTEzYTE4MzVkNTlmZGNmMTdlMDM4NmIwY2JiOGYzXzdfZjFjNTMyMzE="""


def get_clear_keywords_list(keywords_list: List[List[str]]) -> List[List[str]]:
    q = Queue(-1)

    cur_keywords_list = keywords_list.copy()
    # for keywords in keywords_list:
    #     cur_keywords_list.extend(keywords)

    # 先找到所有未收录的关键词
    for start in range(0, len(cur_keywords_list), 15):
        q.put(cur_keywords_list[start:start+15])

    not_exist_keyword_set = set()
    while not q.empty():
        keywords = q.get()
        print(keywords)
        try:
            check_result = check_keywords_exists(keywords, cookies)
            time.sleep(5)
        except:
            traceback.print_exc()
            q.put(keywords)
            time.sleep(90)

        for keyword in check_result["not_exists_keywords"]:
            not_exist_keyword_set.add(keyword)
        print('not_exist_keyword_set', not_exist_keyword_set)

    # 在原有的keywords_list拎出没有收录的关键词
    new_keywords_list = []
    for keywords in keywords_list:
        not_exists_count = len([None for keyword in keywords if keyword in not_exist_keyword_set])
        if not_exists_count == 0:
            new_keywords_list.append(keywords)

    return new_keywords_list


def save_to_excel(datas: List[Dict]):
    pd.DataFrame(datas).to_excel("index.xlsx")


def get_search_index_demo(keywords_list: List[List[str]]):
    """
        1. 先清洗keywords数据，把没有收录的关键词拎出来
        2. 然后split_keywords关键词正常请求
        3. 数据存入excel
    """
    print("开始清洗关键词")
    requested_keywords = []
    keywords_list = get_clear_keywords_list(keywords_list)
    q = Queue(-1)

    for splited_keywords_list in split_keywords(keywords_list):
        q.put(splited_keywords_list)

    print("开始请求百度指数")
    datas = []
    while not q.empty():
        cur_keywords_list = q.get()
        try:
            print(f"开始请求: {cur_keywords_list}")
            for index in get_search_index(
                keywords_list=cur_keywords_list,
                start_date='2022-12-01',
                end_date='2022-12-31',
                cookies=cookies
            ):
                index["keyword"] = ",".join(index["keyword"])
                datas.append(index)
            requested_keywords.extend(cur_keywords_list)
            print(f"请求完成: {cur_keywords_list}")
            time.sleep(10)
        except:
            traceback.print_exc()
            print(f"请求出错, requested_keywords: {requested_keywords}")
            save_to_excel(datas)
            q.put(cur_keywords_list)
            time.sleep(180)

    save_to_excel(datas)


if __name__ == "__main__":
    keywords_list = []

    with open('./term.data', mode='r', encoding='utf8') as f:
        for line in f:
            line = line.strip()
            if line == '':
                continue
            keywords_list.append(line)

    # keywords_list = ['新冠症状']

    get_search_index_demo(keywords_list)