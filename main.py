@@ -0,0 +1,94 @@

# -*- coding: utf-8 -*-

import requests
from urllib.parse import quote
import string
from bs4 import BeautifulSoup
import pandas as pd
import re
import numpy as np
import sys
import os
from urllib import parse
import itertools
import warnings
import jieba
warnings.filterwarnings("ignore")
os.chdir("D:/WWW/ElasticSearch")


wordinput = parse.unquote(sys.argv[1]).encode("utf-8").decode("utf-8")
#wordinput = "设施 番茄 熊蜂 授粉 技术规程"
wordinput = ','.join(jieba.cut_for_search(wordinput)) +"!" +  wordinput
newword = re.split("[\s+\.\!\/_,$%^*(+\"\')]+|[+——()?【】“”！，。？、~@#￥%……&*（）]+", parse.unquote(wordinput))
jingyonglist = ["con", " ", "prn", "aux", "nul", "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
                "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"]
for jingyong in jingyonglist:
    while newword.count(jingyong) > 0:
        newword.remove(jingyong)
while '' in newword:
    newword.remove('')
df = pd.DataFrame(columns=['ID', 'TF_IDF', 'name'])
if len(newword) > 0:
    for word in newword:
        try:
            file = r'./search/' + word + ".txt"
            try:
                f = open(file, encoding='utf-8')
                getdata = np.array(pd.read_table(f, sep=',')).tolist()
                f.close()
                getdata = list(itertools.chain.from_iterable(getdata))
            except IOError:
                url = 'http://www.cibo.cn/search.php?dictkeyword=' + word
                newurl = quote(url, safe=string.printable)
                r = requests.get(newurl)
                r.encoding = 'gbk'
                soup = BeautifulSoup(r.text, "html.parser")
                getdata = [str(word)]
                adm = [str(word)]
                for i in soup("span", class_="font10b"):
                    for j in i.select('a'):
                        adm.extend(re.sub(r'pl\.|vi\.|n\.|v\.|vb\.|pron\.|adj\.|vt\.|adv\.|的复数|ad\.|a\.|-|��', " ",
                                          j.text.lstrip().rstrip()).split(' '))
                getdata.extend(adm[:10])
                while '' in getdata:
                    getdata.remove('')
                adm = getdata
                getdata = list(set(getdata))
                getdata.sort(key=adm.index)
                if len(getdata) > 0:
                    pd.DataFrame(getdata).to_csv(file, sep=',', header=True, index=False)
        except IOError:
            getdata = []
        i = 0
        for keyword in getdata:
            i = i + 1
            file = r'./wordscore/' + str(keyword) + ".txt"
            try:
                f = open(file, encoding='utf-8')
                df1 = pd.read_table(f, sep='\t')
                df1['TF_IDF'] = np.exp(df1['TF_IDF']) / (i*i)
                df1['name'] = keyword
                df = df.append(df1)
                f.close()
            except IOError:
                df1 = pd.DataFrame(columns=['ID', 'TF_IDF', 'name'])
    df = df.dropna()
    minnum = min(df['TF_IDF'])
    df = df.pivot_table(
        index=["ID"],  # 行索引（可以使多个类别变量）
        columns=["name"],  # 列索引（可以使多个类别变量）
        values=["TF_IDF"]  # 值（一般是度量指标）
    )
    df[np.isnan(df)] = minnum
    newdf = np.prod(df, axis=1)
    df = pd.DataFrame(columns=['ID',"TF_IDF"])
    df['ID'] = newdf.index
    df['TF_IDF'] = newdf.values
    maxnum = max(df['TF_IDF']) * 0.0001
    df = df[df['TF_IDF'] > maxnum]
    score = df['TF_IDF'].groupby(df['ID']).sum().reset_index().sort_values(by='TF_IDF', ascending=False)[:1000]
else:
    score = pd.DataFrame(columns=['ID', "TF_IDF"])
print(score.to_json(orient='values'))
