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
nqi_std <- dbGetQuery(con, "SELECT id, chinese_title, english_title, release_date FROM nqi_std") 
```
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;当数据读入到我们的变量空间的时候我们要考虑2件事情一个是时间变量的处理，还有一个是文本的分词。时间变量的处理我打算是直接对数据进行个转换，将其变成一个\[1-2\]的数，距离现在越近数值越大。

### 2.2 日期转数值
```{r}
library(data.table)
nqi_std <- data.table(data)
release_date <- unique(nqi_std[, release_date])
date_to_num <- data.table(cbind(release_date, 
                                num = seq(from = 1+1/length(release_date), to = 2, by = 1/length(release_date))))
setkey(date_to_num, release_date)
setkey(nqi_std, release_date)
nqi_std <- merge(nqi_std, date_to_num)
nqi_std <- nqi_std[, release_date := NULL]
nqi_std <- nqi_std[, num := as.numeric(nqi_std[, num])]
```

