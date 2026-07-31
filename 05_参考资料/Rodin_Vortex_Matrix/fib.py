def fib(n):
    a, b = 0, 1
    for i in range(n):
        a, b = b, a + b
    return a

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


for num in range(1,33):  ### 这个33可以改。
    fib_str=str(fib(num))
    dpd_str=outputresult(fib_str)
    print  '%d: %s         %s ' % (num, fib_str,dpd_str)
