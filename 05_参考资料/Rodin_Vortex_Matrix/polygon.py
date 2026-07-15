import turtle
from turtle import *
def polygon():
    tracer(100)
    for i in range(3,200):
        circle(i*10,steps=i)
        lt(30)
    exitonclick()
polygon()

