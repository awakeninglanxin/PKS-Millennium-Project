from turtle import *
from time import clock, sleep
from math import *
import turtle 
def outputresult(prompt, corner):
    cnt=1
    while True:
        num_final=0
        if cnt==1:
            if prompt.isdigit():
                nums_lst = list(prompt)
            else:
                print 'your prompt is not a digit!!'
                break
        for num in nums_lst:
            num_final+=int(num)
        if num_final<=corner:
            break
        else:
            nums_lst = list(str(num_final))
            cnt+=1
            continue
    return int(num_final)  ### this is output int

def test(c):
    s = Screen()
    s.bgcolor("black")
    color("red")
    begin_fill()
    pensize(1)
    zoom=1  ##u can change this number bigger to zoom in
    speed(100)
##    pos()
    pos_list=[]
    
    penup()
    pos_cnt=0

    corner_list=[]

    c=star(c)
    for num in range (1,c*((c/2)-1),((c/2)-1)):
        if num % c==0:
            corner_list.append(c)
        else:
            corner_list.append(num % c)

##    corner_list=set(corner_list)
##    corner_list=list(corner_list)
    print corner_list
    print len(corner_list)
    while True:
        sub_plist=[]
        forward(500)
        left(180-(360/int(c)))

        sub_plist=[corner_list[pos_cnt],pos()]
        pos_list.append(sub_plist)
        pos_cnt+=1   # just for 12 corner
        if abs(pos()) <1:
            break
    pos_list.sort(key=lambda x: x[0])
    print pos_list
    print "this is the number of corner: ",len(pos_list)
    speed(0)
##    tracer(100)
    number=1
    goto(pos_list[1][1])
##    pendown()
##    for n in range (10000):
##    ht()
    occur_one=0
    file = open('out.txt', 'w')
    string_1=""
    pendown()
    while True:
        number=number*2

        dpd=outputresult(str(number),c)
        if dpd==1:
            print occur_one
            occur_one=0

        file.write(str(dpd)+" ")
        occur_one+=1
        goto(pos_list[dpd][1])        
    exitonclick()
    file.close()


def test2(c):
    number=1
    occur_one=0
    file = open('out number.txt', 'w')
    string_1=""
    while True:
        number=number*2
        dpd=outputresult(str(number),c)
        if dpd==1:
            print occur_one
            occur_one=0
        occur_one+=1
        file.write(str(dpd)+" ")
    file.close()

def star(corner):
    speed(100)
    tracer(100)
##    tracer(2)
    track_num=0
    penup()
    while True:
        forward(600)
        left(180-(360/corner))
        track_num+=1
        if abs(pos()) <1:
            break
    
    return track_num
    exit()

def test3():
    s = Screen()
    s.bgcolor("black")
    color("red")
    begin_fill()
    pensize(1)
    zoom=1  ##u can change this number bigger to zoom in

    speed(1)
    tracer(1)
    number=1
##    ht()
    occur_one=0
##    file = open('out.txt', 'w')
##    string_1=""
    pendown()
    pos_list=[[1, (500.00,0.00)], [2, (500.00,133.97)], [3, (433.01,250.00)], [4, (316.99,316.99)], [5, (183.01,316.99)], [6, (66.99,250.00)], [7, (-0.00,133.97)], [8, (0.00,-0.00)], [9, (66.99,-116.03)], [10, (183.01,-183.01)], [11, (316.99,-183.01)], [12, (433.01,-116.03)]]
    penup()
    goto(pos_list[1][1])
    pendown()
    while True:
        number=number*2

        dpd=outputresult(str(number),12)
        if dpd==1:
            print occur_one
            occur_one=0

##        file.write(str(dpd)+" ")
        occur_one+=1
        print dpd
        goto(pos_list[dpd][1])        
    exitonclick()
    file.close()

    
def main():
##    print (printlst("1","1000","2"))
##    print draw_circle(1)
##    print star(7)
##    print test(12)
##    print test3()
    while 1:
        prompt=raw_input("give me a number:  ")
        print outputresult(prompt, 10)
##    print test2(12)
main()
