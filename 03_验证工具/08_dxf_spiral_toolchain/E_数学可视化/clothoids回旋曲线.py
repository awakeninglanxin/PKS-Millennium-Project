import math
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg

def clothoid_curve(t0, t1, num_points, k):
    """
    Generate points on a Clothoid curve (Euler spiral).
    :param t0: Start parameter value.
    :param t1: End parameter value.
    :param num_points: Number of points to generate.
    :param k: Curvature rate.
    :return: List of Rhino.Geometry.Point3d
    """
    points = []
    delta_t = (t1 - t0) / (num_points - 1)
    for i in range(num_points):
        t = t0 + i * delta_t
        x = simpson_integral(0, t, 100, lambda u: math.cos(k * u**2))
        y = simpson_integral(0, t, 100, lambda u: math.sin(k * u**2))
        points.append(rg.Point3d(x, y, 0))  # Only store x and y for the clothoid points
    return points

def simpson_integral(a, b, n, func):
    """
    Approximate integral of func from a to b using Simpson's rule.
    :param a: Start of the interval.
    :param b: End of the interval.
    :param n: Number of intervals (must be even).
    :param func: Function to integrate.
    :return: Approximation of the integral.
    """
    if n % 2 == 1:
        n += 1
    h = (b - a) / n
    result = func(a) + func(b)
    for i in range(1, n, 2):
        result += 4 * func(a + i * h)
    for i in range(2, n - 1, 2):
        result += 2 * func(a + i * h)
    return result * h / 3

def draw_clothoids(t0, t1, num_points, k1, k2):
    """
    Generate and draw two Clothoid curves with different curvatures (k1 and k2),
    one for arc_position < 0 and another for arc_position > 0.
    The curves are symmetric about the origin.
    :param t0: Start parameter value.
    :param t1: End parameter value.
    :param num_points: Number of points to generate.
    :param k1: Curvature rate for arc_position < 0.
    :param k2: Curvature rate for arc_position > 0.
    """
    # Generate clothoid points for arc_position < 0 with k1
    points_neg = clothoid_curve(t0, 0, num_points, k1)
    # Generate clothoid points for arc_position > 0 with k2
    points_pos = clothoid_curve(0, t1, num_points, k2)

    # Draw the two Clothoid curves in Rhino
    curve_neg = rs.AddInterpCurve([rg.Point3d(pt.X, pt.Y, pt.Z) for pt in points_neg])
    curve_pos = rs.AddInterpCurve([rg.Point3d(pt.X, pt.Y, pt.Z) for pt in points_pos])

    return curve_neg, curve_pos

def main():
    # Parameters for the clothoid
    t0 = -10
    t1 = 10  # Length of the curve
    num_points = 100  # Number of points on the curve
    k1 = 0.5  # Default Curvature rate for arc_position < 0
    k2 = 0.1  # Default Curvature rate for arc_position > 0

    # Draw the two Clothoid curves with different curvatures
    draw_clothoids(t0, t1, num_points, k1, k2)

if __name__ == "__main__":
    main()
