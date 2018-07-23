# 一个简易的智能搜索引擎
  在公司工作的过程中,我构建了一个简易的智能搜索系统，例如搜索番茄的同时也进行了西红柿的查询，也就是简易的联想搜索,具体功能可以进入这个网址进行查看[http://www.hzzlfw.cn/index.php?s=/Home/Standard/staquery/search](http://www.hzzlfw.cn/index.php?s=/Home/Standard/staquery/search)。主要是通过R语言和Python进行实现的。
接下来我会逐步介绍如何实现这个搜索系统。

## 1. 数据存储结构和形式
杭州质量网的标准查询数据存在我们服务器上，这里主要是介绍下数据类型
标准数据包括了
------------ | -------------
id|658860
chinese_title|机动车维修服务客户满意度评价方法
english_title|
release_date|2017-12-30

## 2. 如何计算定义搜索相关度
```R
# 环境清除及工作路径搭建
rm(list = ls())
memory.limit(103430)
setwd("D:/www/ElasticSearch/fencimoxing")
```
