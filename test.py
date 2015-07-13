import os
print os.getcwd()
for eachFile in os.listdir(os.getcwd()):
    print  eachFile
fname=open(raw_input("plz enter file name:"))
try:
    print os.getcwd()
    fobj=open(fname,'r')
except IOError,e:
    print "Error: file open error:",e