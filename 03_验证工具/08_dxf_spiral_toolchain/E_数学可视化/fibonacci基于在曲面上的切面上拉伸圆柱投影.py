import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math

def fibonacci_spiral_sphere(radius, num_points):
    points = []
    num_groups=12
    phi = math.pi * (3. - math.sqrt(5.))  # Golden angle in radians
    
    # Angle step for each group
    group_angle = 2 * math.pi / num_groups  # Divide the circle into 'num_groups' parts
    
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
        
        # Modify phase shift to evenly distribute points for the desired number of groups
        for j in range(num_groups):
            phase_shift = j * group_angle  # Calculate the phase shift for each group
            x_symmetric = -radius_at_z * math.cos(theta + phase_shift)
            y_symmetric = -radius_at_z * math.sin(theta + phase_shift)
            point_symmetric = rg.Point3d(x_symmetric * radius, y_symmetric * radius, z * radius)
            points.append(point_symmetric)
        
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

def create_base_circle_at_point(point, radius):
    # Get the surface parameter at the point
    uv = rs.SurfaceClosestPoint(surface, point)
    
    # Get the tangent vectors at the point on the surface (U and V directions)
    frame = rs.SurfaceFrame(surface, uv)
    if frame:
        frame_origin, tangent_u, tangent_v, normal = frame  # Unpack all four values
    else:
        print("Error: Could not get surface frame at point.")
        return None
    
    # Normalize the tangent vectors
    tangent_u = rs.VectorUnitize(tangent_u)
    tangent_v = rs.VectorUnitize(tangent_v)
    
    # Calculate the four points for the plane
    # Positive and negative directions for tangent_u
    point_u_positive = rs.PointAdd(frame_origin, tangent_u * radius)
    point_u_negative = rs.PointAdd(frame_origin, tangent_u * -radius)
    
    # Positive and negative directions for tangent_v
    point_v_positive = rs.PointAdd(frame_origin, tangent_v * radius)
    point_v_negative = rs.PointAdd(frame_origin, tangent_v * -radius)
    
    # Define the four points (excluding frame_origin)
    four_points = [point_u_positive, point_u_negative, point_v_positive, point_v_negative]
    
    # Create a plane centered at frame_origin
    # Use the normal vector and frame_origin to define the plane
    plane = rg.Plane(frame_origin, normal)
    
    # Create the base circle using the defined plane
    base_circle = rs.AddCircle(plane, radius)
    
    return base_circle


def create_cylinders_at_points(projected_points, radius, height):
    cylinders = []
    for point, direction in projected_points:
        # Get the surface normal at the point where the projection occurred
        uv = rs.SurfaceClosestPoint(surface, point)
        frame = rs.SurfaceFrame(surface, uv)
        if frame:
            frame_origin, tangent_u, tangent_v, normal = frame  # Unpack all four values
        else:
            print("Error: Could not get surface frame at point.")
            continue
        
        # Normalize the surface normal vector
        normal = rs.VectorUnitize(normal)
        
        # Define the sweep path: start at the projected point and extend outward along the normal
        path_start = point  # Start at the projected point
        path_end = path_start + normal * height  # Extend outward along the normal
        path = rs.AddLine(path_start, path_end)
        
        # Create the base circle for the cylinder (using radius 5.05mm as requested)
        base_circle = create_base_circle_at_point(path_end, radius)  # Create the base circle using the cross logic
        
        if base_circle is None:
            continue  # Skip this point if the base circle couldn't be created
        
        # Perform the sweep to create the cylinder
        cylinder = rs.AddSweep1(path, [base_circle], closed=True)
        if cylinder:
            # Cap the cylinder to close the ends
            rs.CapPlanarHoles(cylinder)
            
            # Move the cylinder 3mm in the negative normal direction
            rs.MoveObject(cylinder, -normal * 5)
        
        # Clean up temporary geometry
        rs.DeleteObject(base_circle)
        rs.DeleteObject(path)
        
        if cylinder:
            cylinders.append(cylinder)  # Add the cylinder to the list
        
    return cylinders



# Get the surface from the user
surface_id = rs.GetObject("Select a surface to project the points onto", rs.filter.surface)
if surface_id:
    surface = rs.coercesurface(surface_id)  # Convert to Rhino.Geometry.Surface
    if surface:
        # Parameters
        radius = 100  # Radius of the sphere
        num_points =12  # Number of points to generate
        cylinder_radius = 5.05  # Radius of the cylinder
        cylinder_height = 20# Height of the cylinder

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
            print("{} tubes created at the projected points.".format(len(cylinders)))
        else:
            print("Error projecting points onto the surface.")
    else:
        print("Failed to convert the selected object to a surface.")
else:
    print("No surface selected.")