import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math

# Function to create points on a sphere with symmetric Fibonacci spiral
def fibonacci_spiral_sphere(radius, num_points):
    points = []
    phi = math.pi * (3. - math.sqrt(5.))  # Golden angle in radians
    for i in range(num_points):
        z = 1 - (i / float(num_points - 1)) * 2  # Z-coordinate of the point (originally Y)
        radius_at_z = math.sqrt(1 - z * z)  # Radius of the circle at Z coordinate
        theta = phi * i  # Golden angle step
        
        # Generate points in both positive and negative directions for symmetry
        x_positive = radius_at_z * math.cos(theta)
        y_positive = radius_at_z * math.sin(theta)
        
        # Add the original point in the positive direction
        point_positive = rg.Point3d(x_positive * radius, y_positive * radius, z * radius)
        points.append(point_positive)
        
        # Add the corresponding symmetric point in the negative direction
        x_negative120 = -radius_at_z * math.cos(theta- 2*math.pi/3)  
        y_negative120 = -radius_at_z * math.sin(theta- 2*math.pi/3)
        point_negative120 = rg.Point3d(x_negative120 * radius, y_negative120 * radius, z * radius)
        points.append(point_negative120)
                # Add the corresponding symmetric point in the negative direction
        x_positive120 = radius_at_z * math.cos(theta+ 2*math.pi/3)  
        y_positive120 = radius_at_z * math.sin(theta+ 2*math.pi/3)
        point_positive120 = rg.Point3d(x_positive120 * radius, y_positive120 * radius, z * radius)
        points.append(point_positive120)

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
            # Use the intersection point directly without '.Point'
            intersection_point = intersection_results[0]
            projected_points.append((intersection_point, ray.Direction))  # Store point and ray direction
    return projected_points

# Function to create a cylinder at each projected point using Sweep1
def create_cylinders_at_points(projected_points, radius, height):
    cylinders = []
    for point, direction in projected_points:
        # Create a base circle at the projected point
        plane = rs.PlaneFromNormal(point, direction)  # Define a plane at the point with ray direction as normal
        base_circle = rs.AddCircle(plane, radius)
        
        # Define the path for the sweep (along the ray direction)
        path_start = -direction*0.5
        path_end = point   # Extend along the ray direction
        path = rs.AddLine(path_start, path_end)
        
        # Perform the sweep to create the cylinder
        cylinder = rs.AddSweep1(path, [base_circle], closed=True)
        if cylinder:
            # Cap the cylinder to close the ends
            rs.CapPlanarHoles(cylinder)
            cylinders.append(cylinder)
        
        # Clean up temporary geometry
        rs.DeleteObject(base_circle)
        rs.DeleteObject(path)
    return cylinders

# Get the surface from the user
surface_id = rs.GetObject("Select a surface to project the points onto", rs.filter.surface)
if surface_id:
    surface = rs.coercesurface(surface_id)  # Convert to Rhino.Geometry.Surface
    if surface:
        # Parameters
        radius = 100  # Radius of the sphere
        num_points = 50  # Number of points to generate
        cylinder_radius = 5.06  # Radius of the cylinder
        cylinder_height = 1 # Height of the cylinder

        # Generate Fibonacci spiral points with symmetry
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
            for point, _ in projected_points:
                rs.AddPoint(point)
            print("{} points projected onto the surface successfully!".format(len(projected_points)))

            # Create and display cylinders at each projected point
            cylinders = create_cylinders_at_points(projected_points, cylinder_radius, cylinder_height)
            print("{} cylinders created at the projected points.".format(len(cylinders)))
        else:
            print("Error projecting points onto the surface.")
    else:
        print("Failed to convert the selected object to a surface.")
else:
    print("No surface selected.")
