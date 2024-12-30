abc <- read.table(file.choose(), header = T, sep=",")
mean(abc$age)---using dollar sign to extract variable
attach(abc)---attach abc data to R memory
detach(abc)--- detach abc data from R memory
summary(abc)--- desc of data set
age[11:14]---- 19 17 20 21

Femdat <- abc[Gender=='female', ]  --- gives only female data
dim(Femdat)---  gives dimensions of Femdat -- like 365obs  6vars
xyz <- cbind(abc,Femsmoke)---cbind is used to append a variable to your dataset
rm(list=ls())--- to remove list of all the data objects in R Memory
save.image("yyy.Rdata") --- to save all your code written in worksapce









