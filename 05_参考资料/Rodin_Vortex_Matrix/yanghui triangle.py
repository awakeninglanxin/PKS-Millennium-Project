from turtle import *
def yanghui(NUM):
    for i in range(NUM):
        if i < 2:
            yhList = [1] * (i + 1)
        else:
            yhList[1:-1] = [(tmpNum + yhList[j]) for j, tmpNum in enumerate(yhList[1:])]
        sum_int=0
        for num in yhList:
            sum_int+=num
##            fd(1)  ## try to change the coefficient_int in the blacket manually
        print yhList
        print sum_int

yanghui(20)
