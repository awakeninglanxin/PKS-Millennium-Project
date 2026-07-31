from turtle import *
from time import clock, sleep
from math import *
import turtle
from random import randint
def outputresult(prompt):
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
        if num_final<10:
            break
        else:
            nums_lst = list(str(num_final))
            cnt+=1
            continue
    return int(num_final)  ### this is output int


def randomnum():
    for n in range(20):
        print 'random:  ' ,randint(1,9) 


    
def all_metrix_1to10_difference():
    print 'these are the same difference in every row'
    for num in range(1,11):
        metrix_difference(num)
        
def all_metrix_1to7_ratio():
    print 'these are the same ratio in every row'
    for num in range(1,11):
        metrix_ratio(num)

def make_circle_difference(min_str,step,coefficient_str):
    if min_str.isdigit()==False:
        min_str='3'
    
    if step.isdigit()==False:
        step='3'
    if coefficient_str.isdigit()==False:
        coefficient_str='9'
    coefficient_int=int(coefficient_str)
    file_record = open('record_difference.txt', 'w')
    bgcolor("black")
    step=int(step)
    screensize(4000,3200)
    speed(100)
    sleep(2)
    ht()
    color('blue','gold')
    begin_fill()
    pensize(1)
    tracer(2)
    turn=1
    dpd_sum=0
    min_int=int(min_str)

    while 1:
        cnt=min_int
        t1 = clock()
        itera=1
        while 1:
            dpd=outputresult(str(cnt))  ## u can try to change the cnt, for example, multiple by a coefficient
            dpd=int(dpd)
            fd(dpd*coefficient_int)  ## try to change the coefficient_int in the blacket manually
            rt(dpd*coefficient_int)  ##try to change the coefficient_int in the blacket manually
##            rt(90)
            cnt=((cnt*step+step))
            
            if abs(pos())==0:
                print 'hey! computer code has no problem'

##            itera+=1
##            if (itera%9)==0:
##                fd(randint(1,9))
            if dpd==9:
                fd(randint(1,9))
            
            
    exitonclick()
    file_record.close()

def make_circle_ratio(min_str,ratio_str,coefficient_str):
    itera=1
    if min_str.isdigit()==False:
        min_int=2
    else:
        min_int=int(min_str)
    if ratio_str.isdigit()==False:
        ratio_str='2'
    if coefficient_str.isdigit()==False:
        coefficient_str='4'
        
    coefficient_int=int(coefficient_str)
    file_record = open('record_ratio.txt', 'w')
    bgcolor("black")
    ratio_int=int(ratio_str)
    screensize(4000,3200)
    speed(100)
##    ht()
    color("purple")
    begin_fill()
    pensize(1)

    
    turn=1
    dpd_sum=0
    sleep(2)
    tracer(100)
    while 1:
        onclick(turtle.goto)
        intial=min_int
        t1 = clock()
        while 1:
            dpd=outputresult(str(intial))  ## u can try to change the cnt, for example, multiple by a coefficient
            fd(dpd*coefficient_int*2)  ## try to change the coefficient_int in the blacket manually
            rt(dpd*coefficient_int)  ##try to change the coefficient_int in the blacket manually
##            rt(pow(dpd,coefficient_int))
            intial=intial*ratio_int
            if abs(pos())==0:
                no_error=1
                break
            else:
                no_error=0
                
            if abs(pos())<1:  ### this is the prove of the collape point of the imperfect compute system,
                dpd=dpd*coefficient_int ##try to change the coefficient_int
                dpd_sum+=dpd
                rt(dpd)  #### if u comment this line it will be circle
                print 'the circle turns this much of angle' , dpd
                t2 = clock()
                td=t2-t1
                line=(turn,dpd,td)
                file_record.write(str(line))
                print "the period of the individual circle: {0:.3f} sec".format(td)
                update()
                break
            itera+=1
            if (itera%9)==0:
                fd(randint(1,9)*coefficient_int)
    
##        min_int=fib(min_int)
        print 'it turned',turn
        turn+=1
        if no_error==1:
            print 'no computer error'
            break
        if dpd_sum>=360: 
            break
##        min_int+=1   ## uncommend this, the angle it turn will be the same in average
    
##    end_fill()
    exitonclick()  ### commend this, when you click on the screen , it will not be closed anymore.
    file_record.close()
    


    
def main():

    while 1:
        print 'There are choices: \n d==make circles (equal difference) \n r==make circles (equal ratio)'
        prompt1=raw_input('what do you want: ')
        if 'quit' in prompt1:
              break

        if prompt1=='d':
            prompt_min=raw_input('give me num for min: ')
            step_str=raw_input('give me num for step: ')
            coefficient_str=raw_input('give me num for coefficient: ')
            make_circle_difference(prompt_min,step_str,coefficient_str)
            
        if prompt1=='r':
            prompt_min=raw_input('give me num for min: ')
            ratio_str=raw_input('give me num for ratio: ')
            coefficient_str=raw_input('give me num for coefficient: ')
            make_circle_ratio(prompt_min,ratio_str,coefficient_str)
        

            
            

    print '最后的疑问，看到def make_circle_ratio(min_str,ratio_str): 里面我使用的是if abs(pos())<=1:  pos()是一个代表着坐标，起点是（0,0），abs(pos())意思是\
距离圆点的直线距离。但是这个距离永远不是0，也就是永远回不到圆点，只能无限接近，按道理来讲应该是abs(pos())==0，但是我试了，这个turtle永远无法回到圆点，它就一直在那一个维度转圈，\
进入不了下个维度，我想这一定说明了啥，因为一个有周期的数列，一定会准确回到圆点的，也就是说要么是python 系统的编码出了误差，比如本该走1个单位，它走了0.9999个单位，\
这样的话就不会回到圆点，但我的直觉告诉我，做这个python的公司不会犯这样的低级错误，所以，这个问题是根本性的问题，是整个电脑工业的问题，这也行也是为了避免建立真正的人工智\
能。如果利用vortex math建立一个电脑系统，那么这将在任何维度都会适用，除非你把电脑带出了宇宙。这也是Rodin提到过的。'
main()
