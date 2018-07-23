# 环境清除及工作路径搭建
rm(list = ls())
memory.limit(103430)
setwd("D:/www/ElasticSearch/fencimoxing")
# 引入相关package
library(data.table)
library(jiebaRD)
library(jiebaR)
library(data.table)
library(jiebaRD)
library(jiebaR)
library(RMySQL)
library(readr)
# 设定分词器
# 读取标准
con <- dbConnect(MySQL(),
                 host='60.191.74.66',
                 port=3307,
                 dbname="std_format_wto_info",
                 user="gfs",
                 password="L2JaTK")
dbSendQuery(con,'SET NAMES gbk')

data <- dbGetQuery(con, "SELECT id,chinese_title,english_title,release_date FROM nqi_std")
nqi_std <- data.table::data.table(data)
setkey(nqi_std, release_date)
# 设定分词数据集
text <- data.table(text = paste(nqi_std$chinese_title, 
                                nqi_std$english_title),
                   ID = nqi_std$id)
text0 <- data.table(time = nqi_std$release_date,
                    ID = nqi_std$id)
setkey(text0, time)
replace <- function(x){
  return(ifelse(x=="0000-00-00", "1925-01-01", x))
}
text0 <- text0[, lapply(.SD, replace), by = ID]
text0[, TF_IDF := exp(sort(runif(nrow(text0))))]
text0[, time := NULL]
setkey(text0, ID)
# 数据集分词
cutmix <- worker(type = "mix", user = "dict.txt", stop_word = "stop.txt",encoding = "UTF-8")
cutmp <- worker(type = "mp", user = "dict.txt", stop_word = "stop.txt",encoding = "UTF-8")
cutfull <- worker(type = "full", user = "dict.txt", stop_word = "stop.txt",encoding = "UTF-8")
cutquery <- worker(type = "query", user = "dict.txt", stop_word = "stop.txt",encoding = "UTF-8")

# 分词函数
fenci <- function(x){
  x <- gsub("[[:space:]]|[[:punct:]]|[0-9]", " ", x)
  cut_result1 <- segment(tolower(x), cutmix)# 关键词提取函数
  cut_result2 <- segment(tolower(x), cutmp)# 关键词提取函数
  cut_result3 <- segment(tolower(x), cutfull)# 关键词提取函数
  cut_result4 <- segment(tolower(x), cutquery)# 关键词提取函数
  cut_result <- c(cut_result1,cut_result2,cut_result3,cut_result4)
  cut_result <- unique(cut_result)
  return(cut_result)
}

new <- text[, lapply(.SD, fenci), by = ID]

# 设定主键
setkey(new, ID)

new <- merge(new, text0)
# 清洗变量空间
# a <- ls()
# rm(list = a[which(a!='new')])
print(nrow(new))
# 读取关键词
mykeyword <- unique(new[,text])
mykeyword <- sort(mykeyword)
print(length(mykeyword))
# 设定主键.
fwrite(new, "D:/www/ElasticSearch/new.txt")

setkey(new, text)
Encoding(mykeyword) <- "UTF-8"
setwd("D:/www/ElasticSearch/wordscore")
# 删除原有文件
lf <- list.files(".", pattern = "txt")
file.remove(lf)
# 写入文件函数
writedata <- function(x){
  file <- paste(x, ".txt", sep = "")
  result <- new[list(x)]
  write.table(result[, text := NULL], file, quote = FALSE, row.names = FALSE, fileEncoding = "UTF-8",sep = "\t")
}
# 写入文件
lapply(mykeyword, writedata)
setwd("D:/www/ElasticSearch/fencimoxing")
rm(list=ls())
