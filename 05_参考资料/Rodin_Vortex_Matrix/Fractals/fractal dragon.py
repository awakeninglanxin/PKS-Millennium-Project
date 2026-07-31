import turtle
from functools import partial

nreplacements = 8
angle = 60
step = 5

# generate command
cmd = 'f'
for _ in range(nreplacements):
    cmd = cmd.replace('f', 'f+f-f')

# draw
t = turtle.Turtle()
i2c = {'f': partial(t.forward, step),
       '+': partial(t.left, angle),
       '-': partial(t.right, angle),
}
for c in cmd:
    i2c[c]()
