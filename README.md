# 一个简易的智能搜索引擎
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;在公司工作的过程中,我构建了一个简易的智能搜索系统,具体功能可以进入[杭州质量服务网](http://www.hzzlfw.cn/index.php?s=/Home/Standard/staquery/search)进行查看，这个流程主要是通过R语言和Python进行实现的。接下来我会逐步介绍如何实现这个搜索系统。

## 1. 数据存储结构和形式
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;杭州质量网的标准查询数据存在我们服务器上，以下是我所使用到的数据案例，对于标准查询，领导交给我们的要求是标题匹配，这里我就没有取出正文进行计算。release_date这个变量是为了进行时间加权，领导表示不想看到几十年前的标准。

id|chinese_title|english_title|release_date
------------ | ------------- | ------------- | -------------
659758|制药机械（设备）清洗、灭菌验证导则|Verify guidance of cleaning and sterilization for pharmaceutical machinery|2018/3/15
659638|数字印刷系统的使用要求及检验方法|Use requirements and test methods for digital printing system|2018/3/15
659523|浮法玻璃拉边机|Top roller of float glass|2018/3/15
659430|流体输送用热塑性塑料管道系统 耐内压性能的测定|Thermoplastics piping systems for the conveyance of fluids—Determination of the resistance to internal pressure|2018/3/15
659399|家具中重金属锑、砷、钡、硒、六价铬的评定方法|The assessment method of the heavy metal Sb,As,Ba,Se and Cr（Ⅵ）in furniture|2018/3/15
659398|纺织品 非织造布试验方法 第15部分：透气性的测定|Textiles—Test methods for nonwovens—Part 15: Determination of air permeability|2018/3/15
659403|纺织品 机织物接缝处纱线抗滑移的测定 第2部分：定负荷法|Textiles—Determination of the slippage resistance of yarns at seam in woven fabric—Part 2: Fixed load method|2018/3/15
659397|纺织品 生理舒适性 稳态条件下热阻和湿阻的测定(蒸发热板法)|Textiles－Physiological effects－Measurement of thermal and water-vapour resistance under steady-state conditions(sweating guarded-hotplate test)|2018/3/15
659395|木家具中氨释放量试验方法|Test methods of ammonia emission of wooden furniture|2018/3/15
659406|集成电路倒装焊试验方法|Test methods for flip chip integrated circuits|2018/3/15

## 2. 如何计算定义搜索相关度
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;搜索引擎以前最常用的一个数学模型就是[TF_IDF](https://baike.baidu.com/item/tf-idf/8816134?fr=aladdin),我这里也是套用了这个模型。不过由于领导们的小需求--hh领导要求我们搜索番茄的同时要搜索西红柿，也就是实现同义搜索，也可以说是联想搜素。因此我将用户的输入先进行一个关键词的联想，具体的实现手段放在后面讲解，这部分我先介绍最简单的TF_IDF值的计算，由于这部分内容是刚毕业的时候做的。当时只会R不会python的优化，对几千万篇文章进行处理我的代码运行效率实在太低，所以果断放弃了python。

### 2.1 从数据库中导入数据

```{r}
rm(list = ls())                             # 清洗变量空间
setwd("D:/www/ElasticSearch/fencimoxing")   # 设定工作路径
library(RMySQL)                             # 数据库操作的一个包
con <- dbConnect(MySQL(),
                 host='**.***.**.**',       # ip地址
                 port=****,                 # 端口号
                 dbname="********",         # 数据库名字
                 user="****",               # 数据库的用户名
                 password="*****")          # 数据库的密码
dbSendQuery(con, 'SET NAMES gbk')           # 设定gbk编码，不然中文会乱码
# 从数据库中选取id,chinese_title,english_title,release_date
data <- dbGetQuery(con, "SELECT id, chinese_title, english_title, release_date FROM nqi_std") 
data$text <- paste(data$chinese_title, data$english_title)

```

### 2.2 日期转数值
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;当数据读入到我们的变量空间的时候我们要考虑2件事情一个是时间变量的处理，还有一个是文本的分词。时间变量的处理我打算是直接对数据进行个转换，将其变成一个\[1-2\]的数，距离现在越近数值越大。
```{r}
library(data.table)                         # 导入data.table包 R语言多线程数据清洗包
nqi_std <- data.table(data)                 # 转换为data.table
# 删除"chinese_title", "english_title"2列
nqi_std <- nqi_std[, c("chinese_title", "english_title") := NULL] 
# 提取日期数据并进行升序排序，缺失值和日期较小的值会默认在前面sort函数是这样子的
release_date <- sort(unique(nqi_std[, release_date]))
# seq(...)这里是产生了等间隔的数值，分布为1-2
date_to_num <- data.table(cbind(release_date, 
                                dateweight = seq(from = 1+1/length(release_date), to = 2, by = 1/length(release_date))))
setkey(date_to_num, release_date)           # 设定主键release_date
setkey(nqi_std, release_date)               # 设定主键release_date
nqi_std <- merge(nqi_std, date_to_num)      # 主键相同的表才可以合并
nqi_std <- nqi_std[, release_date := NULL]  # 日期数据已经没用了可以直接去除
# 由于r语言cbind后产生的是是矩阵，要求的数据类型为一样，故dateweight变成了一堆字符串，这里需要进行转换
nqi_std <- nqi_std[, dateweight := as.numeric(nqi_std[, dateweight])]

```
### 2.3 定义一个分词器
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;由于某某领导的病态要求：我们这个一定要好好弄像什么凡尔滨对虾啊，秋叶葵啊，这些正常人都不知道的名词也要好好地给我分词分出来。没办法啊，我们只能去把整个搜狗细胞词库拉下来，然后整理了接近5000万条的词库。包含了“腓骨钢板钛合金”，“肺吸虫抗体检测试剂”等等这样的词语，终于基本满足了领导的病态需求。搜狗细胞词库的转换代码我是参考的qinwf开发的cidian包,请移步其[个人主页](https://github.com/qinwf)查看具体实现原理。注意这个包不能再64位R上运行和安装，请用32位的运行。

```{r}
library(jiebaR)
cutquery <- worker(type = "query",          # 定义切词模式，我经过多次尝试，觉得这种最合适
                   user = "dict.txt",       # 个人词库
                   stop_word = "stop.txt",  # 停止词词库
                   encoding = "UTF-8")      # 文件编码
# 分词函数
fenci <- function(x){
  # 将文字中的空白字符，数字，标点符号都替换为空格，替换为空格就是变成分隔符，
  x <- gsub("[[:space:]]|[[:punct:]]|[[:xdigit:]]", " ", x) 
  # 进行分词
  cut_result <- segment(tolower(x), cutquery)
  return(cut_result)
}
```
### 2.4 分词并计算TF_IDF值
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;直接进行TF_IDF值的计算并用权重加权。
```{r}
# 保留id和dateweight属性下进行分词
nqi_std <- nqi_std[, lapply(.SD, fenci), by = .(id, dateweight)]
nqi_std[, count2 := .N, by = id]            # 计算每个标准的词语数量
nqi_std[, count3 := .N, by = .(id, text)]   # 计算每个词语在当前文档中的出现数量
nqi_std <- unique(nqi_std)                  # 去重后才能计算词语在所有文档中出现的文档个数
nqi_std[, count1 := .N, by = text]          # 计算词语在所有文档中出现的文档个数
papercount <- nrow(data)                    # 计算文档个数
nqi_std[, TF_IDF := count3/count2 * log(papercount/(count1+1) * dateweight)]
# TF = count3/count2, IDF = log(papercount/(count1+1)
```

### 2.5 分词结果导出
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;将所有的分词结果按词语名导出到某个固定文件夹路径下。
```{r}
setkey(nqi_std, text)                       # 设定text主键，方便后续操作
mykeyword <- unique(nqi_std[,text])         # 关键词去重
Encoding(mykeyword) <- "UTF-8"              # 设置编码，否则无法写出中文文件
setwd("D:/www/ElasticSearch/wordscore")     # 设定工作路径
lf <- list.files(".", pattern = "txt")      # 查看所有txt文件
file.remove(lf)                             # 删除原有文件
# 写入文件函数
writedata <- function(x){
  file <- paste(x, ".txt", sep = "")        # 设定新产生的文件名
  result <- nqi_std[list(x)]                # 筛选符合条件的数据
  write.table(result[, text := NULL], file, quote = FALSE, row.names = FALSE, fileEncoding = "UTF-8",sep = "\t")  
}
# 写入文件
lapply(mykeyword, writedata)
rm(list=ls())                               # 释放内存
```

```python
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
```
### 3.1 定义分词程序
这里由于没空搭建分词环境就直接调用了某在线分词系统
```python
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
```
### 3.2 定义同义词获取程序
```python
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
```
### 3.3 主模型
```python
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
```
