from turtle import *
from time import clock, sleep
from math import *
import turtle 
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


def printlst(prompt_min,prompt_max,prompt_step):
    list_dpd=[]
    track=1
    track_every9nums=[]
    for number in range(int(prompt_min),int(prompt_max)+1,int(prompt_step)):
        decimal_parity_digit=outputresult(str(number))
        list_dpd.append(decimal_parity_digit)
        if track % 9 ==0:
            track_every9nums.append(decimal_parity_digit)
        track+=1
    return (list_dpd)

def star36(corner):
    s = Screen()
    s.bgcolor("white")
    sleep(1)
    ht()
    if corner.isdigit()==False:
        corner=36
    color('red', 'yellow')
    begin_fill()
    if corner>12:
        tracer(2)
    while True:
        forward(600)
        left(180-(360/int(corner)))
        if abs(pos()) <1:
            break
##    end_fill()
    exitonclick()
    
def metrix_difference(min1_int):
    interval=1
    print 'here is the 10*10 metrix start from ',min1_int,':'
    while 1:
        start=min1_int
        str_lst=[]
        str_inlst=''
        while 1:
            dpd=outputresult(str(start))
            str_inlst+=str(dpd)+'  '
            str_lst.append(dpd)
            start+=interval
            if len(str_lst)==10:
                interval+=1
                break
        print str_inlst
        if interval>10:
            break



def metrix_ratio(min1_int):
    ratio=1
    print 'here is the 10*7 metrix start from ',min1_int,':'
    while 1:
        start=min1_int
        str_lst1=[]
        str_inlst1=''
        while 1:
            dpd=outputresult(str(start))
            str_inlst1+=str(dpd)+'  '
            str_lst1.append(dpd)
            start=start*ratio
            if len(str_lst1)==7:
                ratio+=1
                break
        print str_inlst1
        if ratio>10:
            break

def metrix_rodin_mirror(min2_str):
    if min2_str.isdigit()==False:
        min2_str='1'
    min2_int=int(min2_str)
    increase=1
    cnt=1
    print 'here is the 10*10 metrix start from' , min2_int,':'
    while 1:
        start=min2_int
        str_lst2=[]
        str_inlst2=''
        while 1:
            start=min2_int*increase
            dpd=outputresult(str(start))
            str_inlst2+=str(dpd)+'  '
            str_lst2.append(dpd)
            increase+=1
            if len(str_lst2)==10:
                min2_int+=1
                increase=1
                cnt+=1
                break
        print str_inlst2
        if cnt>10:
            break
    

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
    print '\nThe circle explain how god creat the universe, imagine the num represent the hands of god or Tao or the origin force that cause the big bang\
    , the turtle curve start from the origin position (0,0) it can represent the origin of the universe, and then as the number increase which means\
    the force increase, the energy level increase, so the energy influence the time and space at the same time, think about turtle.fd(num), num =the force of god\
    it represent time, the line it draw represent 1D,the angle it bend to represent the influence to the next denmension.We all know that time is created by shift from \
    space to space, now change of the angle means change from 1 line (1D) to another 1D, but at least u need to be in 2D in order to see the change, after it \
    magically complete a circle which is the door to the next dimension. no matter how strong is the force of god  which in here is step, the shape is never change. '
    print '\n一生二，二生三，三生万物。一个点移动时，我可以把这个点叫宇宙的原始中心，点移动自然成为一条线，当一条线移动时，自然产生二维世界，在这里随着时空的变化，数字让前进的单位形成圆，\
    继续按这个规律，又形成了一大圆，也就是成了圆环，在2D的平面尽然形成了看似3d的圆环，意味着，这个道理不仅在一维适用，二维适用，当然三维也适用，最后你会发现这个理在三维以上能够继续适用，这才是宇宙最终万能公式。\n'
    
    while 1:
        cnt=min_int
        t1 = clock()
        while 1:
            dpd=outputresult(str(cnt))  ## u can try to change the cnt, for example, multiple by a coefficient
            dpd=int(dpd)
            fd(dpd*coefficient_int*4)  ## try to change the coefficient_int in the blacket manually
            rt(dpd*coefficient_int)  ##try to change the coefficient_int in the blacket manually
            cnt+=step
            if abs(pos())==0:
                print 'hey! computer code has no problem'
            if abs(pos())<0.00001: ### this is the prove of the collape point of the imperfect compute system: uncertainty around 0.000000000001 per circle
                rt(dpd)  #### if u comment this line it will be circle
                dpd_sum+=dpd
                print 'the circle turns this much of angle' , dpd
                t2 = clock()
                td=t2-t1
                line=(turn,dpd,td)
                file_record.write(str(line))
                print "the period of the individual circle: {0:.3f} sec".format(td)

                update()
                break
        print 'it turned',turn
        turn+=1
        if dpd_sum>=360: 
            break
##    end_fill()
##        min_int+=1   ## uncommend this, the angle it turn will be the same in average
    exitonclick()
    file_record.close()

def make_circle_ratio(min_str,ratio_str,coefficient_str):
    
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
    speed(10)
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
    
def mn_eck(p, ne,sz):
    turtlelist = [p]
    for i in range(1, ne):
        q = p.clone()
        q.rt(360.0/ne)
        turtlelist.append(q)
        p = q
    for i in range(ne):
        c = abs(ne/2.0-i)/(ne*.7)
        for t in turtlelist:
            t.rt(360./ne)
            t.pencolor(1-c,0,c)
            t.fd(sz)



def show_vortex():
    s = Screen()
    s.bgcolor("black")
    p=Turtle()
    p.pencolor("red")
    p.pensize(3)
    p.speed(1)

    s.tracer(1,10)
#    print p.speed(), p.delay()

    at = clock()
    mn_eck(p, 13,39)   # or: (7,60)
    et = clock()
    exitonclick()
    return "Laufzeit: {0:.3f} sec".format(et-at)


def mn_eck(p, ne,sz):
    turtlelist = [p]
    #create ne-1 additional turtles
    for i in range(1, ne):
        q = p.clone()
        q.rt(360.0/ne)
        turtlelist.append(q)
        p = q
    for i in range(ne):
        c = abs(ne/2.0-i)/(ne*.7)
        # let those ne turtles make a step
        # in parallel:
        for t in turtlelist:
            t.rt(360./ne)
            t.pencolor(1-c,0,c)
            t.fd(sz)

def draw_vortex():
    s = Screen()
    s.bgcolor("black")
    p=Turtle()
    p.speed(0)
    p.hideturtle()
    p.pencolor("red")
    p.pensize(3)

    s.tracer(36,0)

    at = clock()
    mn_eck(p, 36, 19)
    et = clock()
    z1 = et-at

    sleep(1)

    at = clock()
    while any([t.undobufferentries() for t in s.turtles()]):
        for t in s.turtles():
            t.undo()
    et = clock()
    return "Laufzeit: {0:.3f} sec".format(z1+et-at)

def fib(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n-1) + fib(n-2)

def draw_fib(rangeof_n):
    s = Screen()
    s.bgcolor("black")
    color("red")
    begin_fill()
    tracer(100)
    pensize(1)
    zoom=1  ##u can change this number bigger to zoom in
    if rangeof_n.isdigit()==False:
        rangeof_n='30'
    rangeof_n=int(rangeof_n)
    for num in range(rangeof_n):
        length=fib(num)
        forward(length*zoom) 
        right(90)
    penup()
    goto(0,-zoom)
    right(90)
    pendown()
    
    for num in range(rangeof_n):
        length=fib(num)
        circle(-length*zoom,90)
    exitonclick()

def demo():
    print 'this is a Demo: (I am gonna show every kind of function) \n'
    print '\nif u prompt 1, I can calculate decimal parity digit for u. E.g. if u input this incredibly big number 396678524423, I can \
immediately give u the answer, which is '
    t1=clock()
    print outputresult('396678524423')
    t2=clock()
    print "\nIt only spend me about: {0:.3f} sec to do the math\n".format(t2-t1)
    
    print '\nif u prompt 2,and input 4 for example, u will get these\n'
    metrix_difference(4)
    print '\nif u prompt 8,and input 2 for example, u will get these\n'
    metrix_ratio(2)
    print '\nif u prompt 12,  then prompt anynum e.g. 1, u will get a metrix in mirror\n'
    metrix_rodin_mirror('1')
    print '\nif u prompt 9, u going to get 10 metrix(10*7) with different number to begin with, and u will find the cycle in it.\n'
    all_metrix_1to7_ratio()
    print '\nif u prompt 6, u going to get 10 metrix(10*10) with different number to begin with, and u will find the cycle in it.\n'
    print '\nif u prompt 7, and next prompt 3, then prompt 3 , and 3 again, u will get\n'
    make_circle_difference('3','3','3')

    print '\nif u prompt 10, and next prompt 2, then prompt 2 , and last prompt is 8, u will get\n'
    make_circle_ratio('2','2','8')
    print '\nif u prompt 11,  then prompt 20, u will get a fibonacci sequence\n, don\'t prompt big number, the program will crash, within 20 is good'
    draw_fib('20')

    print '\nif u prompt 4, it show the vortex directly and 3 show u how the program draw a vortex\n'
    draw_vortex()
    print '\nif u prompt 5,  then prompt 36, u will get the shape of 12 starship rodin coil\n'
    star36('36')
    
    
def main():
    while 1:
        print 'There are three choices: \n 1==prompt any num \n 2== make a metrix (equal difference) \n 3== show vortex\
\n 4== draw vortex quickly \n 5== draw star \n 6== print metrix in form of 10*10 from 1 to 10 (equal difference)\n 7== make circles (equal difference)\
\n 8 == make a metrix (equal ratio) \n 9 == print metrix in form of 10*7 from 1 to 10 (equal ratio) \n 10== make circles (equal ratio) \n \
11 == draw fibonacci \n 12 == draw a metrix in mirror \nif u need help just type d\n'
        prompt1=raw_input('what do you want: ')
        if 'quit' in prompt1:
              break
        if prompt1=='1':
            prompt2=raw_input('what number?')
            decimal_parity_digit=outputresult(prompt2)
            print decimal_parity_digit
        if prompt1=='2':
            prompt_min=raw_input('give me num for min: ')
            if prompt_min.isdigit()==False:
                prompt_min=1
            
            metrix_difference(int(prompt_min))
                
            print 'look at the column and row u will understand why the circle is formed!'
            print 'the cycle of those numbers are 9 for the row but it is every 3 row the num of cycle get down to 3, and every 9 row , the cycle get down to 1'


        if prompt1=='3':
            print show_vortex()
        if prompt1=='4':
            print draw_vortex()
        if prompt1=='5':
            corner_prompt_str=raw_input('how many corner u want?')
            star36(corner_prompt_str)
        if prompt1=='6':
            all_metrix_1to10_difference()
        if prompt1=='7':
            prompt_min=raw_input('give me num for min: ')
            step_str=raw_input('give me num for step: ')
            coefficient_str=raw_input('give me num for coefficient: ')
            make_circle_difference(prompt_min,step_str,coefficient_str)
        if prompt1=='8':
            min1_int=raw_input('give me num for min: ')
            if min1_int.isdigit()==False:
                min1_int=1
            metrix_ratio(min1_int)
        if prompt1=='9':
            all_metrix_1to7_ratio()
        if prompt1=='10':
            prompt_min=raw_input('give me num for min: ')
            ratio_str=raw_input('give me num for ratio: ')
            coefficient_str=raw_input('give me num for coefficient: ')
            make_circle_ratio(prompt_min,ratio_str,coefficient_str)
        if prompt1=='11':
            rangeof_n=raw_input('give me range of num: ')
            draw_fib(rangeof_n)
        if prompt1=='12':
            min2_str=raw_input('give me min num: ')
            metrix_rodin_mirror(min2_str)
        if prompt1.lower() in ['d','demo','animation','help']:
            demo()
            

    print '最后的疑问，看到def make_circle_ratio(min_str,ratio_str): 里面我使用的是if abs(pos())<=1:  pos()是一个代表着坐标，起点是（0,0），abs(pos())意思是\
距离圆点的直线距离。但是这个距离永远不是0，也就是永远回不到圆点，只能无限接近，按道理来讲应该是abs(pos())==0，但是我试了，这个turtle永远无法回到圆点，它就一直在那一个维度转圈，\
进入不了下个维度，我想这一定说明了啥，因为一个有周期的数列，一定会准确回到圆点的，也就是说要么是python 系统的编码出了误差，比如本该走1个单位，它走了0.9999个单位，\
这样的话就不会回到圆点，但我的直觉告诉我，做这个python的公司不会犯这样的低级错误，所以，这个问题是根本性的问题，是整个电脑工业的问题，这也行也是为了避免建立真正的人工智\
能。如果利用vortex math建立一个电脑系统，那么这将在任何维度都会适用，除非你把电脑带出了宇宙。这也是Rodin提到过的。'
main()
