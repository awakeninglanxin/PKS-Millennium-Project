import trimesh

# Load the mesh
mesh = trimesh.load_mesh('your_mesh.obj')

# Give the mesh thickness
thickness = 0.1  # Specify the thickness value

# Perform the inflation
inflated_mesh = trimesh.creation.offset_faces(mesh, distance=thickness)

# Save the inflated mesh
inflated_mesh.export('inflated_mesh.obj')
