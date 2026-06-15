import rhinoscriptsyntax as rs
import math

def create_clothoid(start1, start2, end1, end2, length):
    """
    Create a 3D clothoid curve between two sets of points.
    :param start1: First point of the starting segment (x, y, z)
    :param start2: Second point of the starting segment (x, y, z)
    :param end1: First point of the ending segment (x, y, z)
    :param end2: Second point of the ending segment (x, y, z)
    :param length: Total curve length
    """
    # Extract coordinates from input
    x1, y1, z1 = start1
    x2, y2, z2 = start2
    x3, y3, z3 = end1
    x4, y4, z4 = end2

    # Calculate starting and ending curvature from the two segments
    # Start vector
    dx_start = x2 - x1
    dy_start = y2 - y1
    dz_start = z2 - z1
    start_length = math.sqrt(dx_start**2 + dy_start**2 + dz_start**2)
    curvature_start = 1 / start_length if start_length != 0 else 0  # Avoid division by zero

    # End vector
    dx_end = x4 - x3
    dy_end = y4 - y3
    dz_end = z4 - z3
    end_length = math.sqrt(dx_end**2 + dy_end**2 + dz_end**2)
    curvature_end = 1 / end_length if end_length != 0 else 0  # Avoid division by zero

    # Direction vectors for the overall curve
    dx_curve = (x3 - x1)
    dy_curve = (y3 - y1)
    dz_curve = (z3 - z1)
    total_distance = math.sqrt(dx_curve**2 + dy_curve**2 + dz_curve**2)

    # Unit direction vectors
    dx_curve /= total_distance
    dy_curve /= total_distance
    dz_curve /= total_distance

    # Generate clothoid points
    t_values = [i / 100.0 for i in range(101)]  # 101 sample points along the curve
    points = []
    delta_curvature = curvature_end - curvature_start

    for t in t_values:
        # Arc length
        s = t * length

        # Current curvature
        curvature = curvature_start + delta_curvature * t

        # Calculate local displacements
        local_x = s * math.cos(curvature)
        local_y = s * math.sin(curvature)

        # Map local displacements to 3D space
        x = x1 + local_x * dx_curve - local_y * dy_curve
        y = y1 + local_x * dy_curve + local_y * dx_curve
        z = z1 + s * dz_curve  # Linear interpolation for Z

        points.append((x, y, z))

    # Add the 3D curve in Rhino
    rs.AddInterpCurve(points)

# Example usage
start1 = (3.078, -0.551, 39.556)
start2 = (3.100,-0.468,39.458
)
end1 = (-34.050, -82.205, 5.390)
end2 = (-34.051,-82.070,5.295)
length = 60

create_clothoid(start1, start2, end1, end2, length)
