import rhinoscriptsyntax as rs
import math

def generate_de_broglie_wave(curve, amplitude=1, frequency=1, phase=0):
    # Get the points of the curve
    points = rs.CurvePoints(curve)
    if not points:
        return None

    # Generate the wave based on the points from the curve
    wave_points = []
    
    for i, point in enumerate(points):
       
        k = 6  # wave number
        x = amplitude * math.cos(k * point[0] + phase)  # y-value of the wave, varies with x
        y= amplitude * math.sin(k * point[1] + phase) 
        # Generate the new wave points, keeping the z-coordinate constant
        wave_points.append([x, y,point[2]])  # Adjust y, keep z unchanged
    
    # Create a new curve by connecting all the wave points
    wave_curve = rs.AddCurve(wave_points)
    return wave_curve

# Example: Select a curve and generate the de Broglie wave
curve = rs.GetObject("Select a curve to generate the de Broglie wave", rs.filter.curve)
if curve:
    amplitude = 1  # Wave amplitude
    frequency =66  # Frequency
    phase = 0  # Initial phase
    
    # Generate the wave
    generate_de_broglie_wave(curve, amplitude, frequency, phase)
