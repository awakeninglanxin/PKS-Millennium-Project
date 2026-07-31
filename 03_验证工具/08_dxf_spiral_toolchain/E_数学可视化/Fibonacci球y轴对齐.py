import rhinoscriptsyntax as rs
import math
import Rhino.Geometry as rg

# Function to create points on a sphere
def fibonacci_spiral_sphere(radius, num_points):
    points = []
    phi = math.pi * (3. - math.sqrt(5.))  # Golden angle in radians
    for i in range(num_points):
        y = 1 - (i / float(num_points - 1)) * 2  # Y-coordinate of the point
        radius_at_y = math.sqrt(1 - y * y)  # Radius of the circle at Y coordinate
        theta = phi * i  # Golden angle step
        x = radius_at_y * math.cos(theta)  # X-coordinate
        z = radius_at_y * math.sin(theta)  # Z-coordinate
        point = rg.Point3d(x * radius, y * radius, z * radius)
        points.append(point)
    return points

# Function to project points onto a surface using rays
def project_points_to_surface(points, surface):
    projected_points = []
    origin = rg.Point3d(0, 0, 0)  # Origin point
    for point in points:
        # Create a ray from the origin through the point
        direction = rg.Vector3d(point)  # Convert point to a vector
        ray = rg.Ray3d(origin, direction)
        # Intersect the ray with the surface
        intersection_results = rg.Intersect.Intersection.RayShoot(ray, [surface], 1)
        if intersection_results:
            # Use the intersection point directly
            intersection_point = intersection_results[0]
            projected_points.append(intersection_point)
    return projected_points


# Get the surface from the user
surface_id = rs.GetObject("Select a surface to project the points onto", rs.filter.surface)
if surface_id:
    surface = rs.coercesurface(surface_id)  # Convert to Rhino.Geometry.Surface
    if surface:
        # Parameters
        radius = 10  # Radius of the sphere
        num_points = 660  # Number of points to generate

        # Generate Fibonacci spiral points
        points = fibonacci_spiral_sphere(radius, num_points)

        # Create the original Fibonacci spiral line
        original_spiral = rs.AddPolyline(points)
        if original_spiral:
            print("Original Fibonacci spiral line created successfully!")
        else:
            print("Error creating original Fibonacci spiral line.")

        # Project points onto the surface using rays
        projected_points = project_points_to_surface(points, surface)

        # Draw the projected points on the surface
        if projected_points:
            for point in projected_points:
                rs.AddPoint(point)
            print("{} points projected onto the surface successfully!".format(len(projected_points)))
        else:
            print("Error projecting points onto the surface.")
    else:
        print("Failed to convert the selected object to a surface.")
else:
    print("No surface selected.")