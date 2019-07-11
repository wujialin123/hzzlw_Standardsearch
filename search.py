# -*- coding: utf-8 -*-                 # 设定utf-8编码
import os                               # 修改工作路径
import warnings                         # 屏蔽警告
import requests                         # request库爬虫
import re                               # 正则表达式库
import pandas as pd                     # dataframe处理
from urllib import parse                # url编码
from urllib.parse import quote
from urllib.parse import unquote
import numpy as np                      # 数据处理
import string                           # 编码转换
from bs4 import BeautifulSoup           # 网页解析
import sys                              # 输入转义
warnings.filterwarnings("ignore")       # 无视警告
os.chdir("D:/WWW/ElasticSearch")        # 修改工作路径

def gethtmltext(word):
    # 抓取分词结果
    try: # 尝试调取 120.26.6.172的分词结果，如果失败了换个ip调取
        url = 'http://120.26.6.172/get.php?source=' + word + '&param1=0.25&param2=0'
        r = requests.get(url, headers={"user-agent": "Mozilla/5.0"})
    except IOError:
        url = 'http://114.67.84.223/get.php?source=' + word + '&param1=0.25&param2=0'
        r = requests.get(url, headers={"user-agent": "Mozilla/5.0"})
    # html文本处理
    keyword = re.split("\r\n", r.text)
    # 删除无效词语，这些都是系统关键词 不能使用
    jingyonglist = ["con", " ", "prn", "aux", "nul", "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8",
                    "com9", "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"]
    for jingyong in jingyonglist:
        while keyword.count(jingyong) > 0:
            keyword.remove(jingyong)
    # 删除多余的空白文字
    while '' in keyword:
        keyword.remove('')
    return np.array(keyword)

def getsynonym(word):
    file = r'./search/' + word + ".txt"
    # 第一步尝试从本地读取
    try:
        openfile = open(file, encoding='utf-8')
        getdata = np.loadtxt(openfile, dtype= np.str)
        openfile.close()
    # 如果本地不存在的话会报错就去网页上抓取近义词
    except IOError:
        url = 'http://www.cibo.cn/search.php?dictkeyword=' + word
        newurl = quote(url, safe=string.printable)
        r = requests.get(newurl)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, "html.parser")
        adm = [str(word)]
        for i in soup.find_all("span"):
            for j in i.select('a'):
                # 词语都存在网页链接上了
                hrefword = unquote(j.get("href"), encoding="GBK")[42:].lower()
                hrefword = re.sub(r'pl\.|vi\.|n\.|v\.|vb\.|sb\.|\'s|pron\.|adj\.|vt\.|adv\.|的复数|ad\.|a\.|phr\.|-|\(|\)|\\ ', "",hrefword)
                hrefword = re.sub(r'&|/|\.',"+", hrefword).split('+')
                adm.extend(hrefword)
        # 删除空白字符
        while '' in adm:
            adm.remove('')
        # 在不修改顺序的情况下去重
        adm_fuzhu = adm
        adm_fuzhu = list(set(adm_fuzhu))
        adm_fuzhu.sort(key=adm.index)
        # 这个词语可能没有被收录，所以这里需要个判断语句，不然会报错
        if len(adm_fuzhu) > 0:
            pd.DataFrame(adm_fuzhu[:5]).to_csv(file, sep=',', header=True, index=False)
        getdata = np.array(adm_fuzhu[:5])
    return getdata
wordinput = parse.unquote(sys.argv[1]).encode("utf-8").decode("utf-8")  # 用户输入请求
newword = gethtmltext(wordinput)                                        # 抓取分词结果
data = pd.DataFrame(columns=['id', 'TF_IDF', 'name'])                   # 设定结果dataframe
try:
    for x in newword:                                                   
        synonym = getsynonym(x)[1:]                                     # 抓取该词语的近义词
        k = 0
        for keyword in synonym:
            k = k + 1
            file = r'./wordscore/' + str(keyword) + ".txt"
            try:
                f = open(file, encoding='utf-8')
                df = pd.read_table(f, sep='\t')
                df['TF_IDF'] = np.exp(df['TF_IDF']) / (k * k * k)       # 读取该词语的所有近义词的数据并加权值
                df['name'] = keyword
                data = data.append(df)
                f.close()
            except IOError:
                data = data
    data = data.dropna()                                                # 删除缺失数据
    data = data.pivot_table(                                            # 做列联表
        index=["id"],  # 行索引（可以使多个类别变量）
        columns=["name"],  # 列索引（可以使多个类别变量）
        values=["TF_IDF"]  # 值（一般是度量指标）
    )
    data = data + 1                                                     # 防止结果太小就整体加1
    data[np.isnan(data)] = 0.5                                          # 如果不存在这个词给0.5分，负向得分
    newdata = np.prod(data, axis=1)                                     # 所有词语得分的总乘积
    data = pd.DataFrame(columns=['ID', "TF_IDF"])                       
    data['ID'] = newdata.index                                          # 读取index 就是文章id
    data['TF_IDF'] = newdata.values                                     # 读取具体得分
    maxnum = max(data['TF_IDF']) * 0.0001                               # 筛选得分较高的文章
    data = data[data['TF_IDF'] > maxnum]                              
    # 将前1000条结果打印出来传输给浏览器
    score = data['TF_IDF'].groupby(data['ID']).sum().reset_index().sort_values(by='TF_IDF', ascending=False)[:1000]
except:
    score = pd.DataFrame(columns=['ID', "TF_IDF"])
print(score.to_json(orient='values')) # 输出传给网页