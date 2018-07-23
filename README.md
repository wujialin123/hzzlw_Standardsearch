# 一个简易的智能搜索引擎
  在公司工作的过程中,我构建了一个简易的智能搜索系统，例如搜索番茄的同时也进行了西红柿的查询，也就是简易的联想搜索,具体功能可以进入这个网址进行查看[http://www.hzzlfw.cn/index.php?s=/Home/Standard/staquery/search](http://www.hzzlfw.cn/index.php?s=/Home/Standard/staquery/search)。主要是通过R语言和Python进行实现的。
接下来我会逐步介绍如何实现这个搜索系统。

## 1. 数据存储结构和形式
杭州质量网的标准查询数据存在我们服务器上，以下是我所使用到的数据案例，对于标准查询，领导交给我们的要求是标题匹配，这里我就没有取出正文进行计算。release_date这个变量是为了进行时间加权，领导表示不想看到几十年前的标准。

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
```R
# 环境清除及工作路径搭建
rm(list = ls())
memory.limit(103430)
setwd("D:/www/ElasticSearch/fencimoxing")
```
