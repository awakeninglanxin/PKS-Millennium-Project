import ezdxf
import numpy as np
import matplotlib.pyplot as plt
from numpy.polynomial import Polynomial
import sys
sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD as App
import Part
# Define the parametric equations
def curve1(t):
    x = 1.618**(-t/(90*np.pi/180)) * np.sin(t) * 1.618 * 2.618
    y = 1.618**(-t/(90*np.pi/180)) * np.cos(t) * 1.618 * 2.618
    z = 0
    return x, y, z

def curve2(t):
    x = 1.618**(-t/(120*np.pi/180)) * np.sin(t) * 1.618
    y = 1.618**(-t/(120*np.pi/180)) * np.cos(t) * 1.618
    z = 0
    return x, y, z

def curve3(t):
    x = 1.618**(-t/(180*np.pi/180)) * np.sin(t)
    y = 1.618**(-t/(180*np.pi/180)) * np.cos(t)
    z = 0
    return x, y, z

# Time intervals
t1 = np.linspace(4*np.pi, 6*np.pi, 400)
t2 = np.linspace(2*np.pi, 4*np.pi, 400)
t3 = np.linspace(0, 2*np.pi, 400)

# Generate points for each curve
points_curve1 = [curve1(t) for t in t1]
points_curve2 = [curve2(t) for t in t2]
points_curve3 = [curve3(t) for t in t3]

# 创建FreeCAD文档
doc = App.newDocument("3DSpiral")
# Add new entities to the modelspace
msp = doc.modelspace()

# Draw the curves by adding Polylines
msp.add_polyline2d(points_curve1)
msp.add_polyline2d(points_curve2)
msp.add_polyline2d(points_curve3)

# Save the DXF document as DWG format (DXF first, then convert to DWG)
dxf_path = "parametric_curves.dxf"
doc.saveas(dxf_path)
