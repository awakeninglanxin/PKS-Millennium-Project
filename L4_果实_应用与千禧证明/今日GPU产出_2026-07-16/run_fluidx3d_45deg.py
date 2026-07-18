"""FluidX3D 仿真 — 双曲直锥漏斗45° (Re=150, 水)"""
import fluidx3d, os

# STL path
STL = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\05_参考资料\几种漏斗stl文件\双曲直锥漏斗45°.stl"
assert os.path.exists(STL), f"STL not found: {STL}"

config = fluidx3d.Config()
config.parse_args([
    '--D3Q27',                    # 27-speed lattice (best accuracy)
    '--FP16S',                    # Half precision (2x faster)
    '--SRT',                      # Single Relaxation Time
    '--GRAPHICS',                 # Interactive 3D window
    '--window',                   # Windowed mode
    '--EQUILIBRIUM_BOUNDARIES',   # Inlet/outlet BCs
    '--UPDATE_FIELDS',            # Show velocity/density
    '-f', STL,                    # STL geometry
    '-r', '2000',                 # Resolution ~2GB VRAM
    '-u', '3.0',                  # Inflow velocity m/s
    '--re', '150',                # Reynolds number
    '--rho', '1000',              # Water density kg/m3
    '--secs', '10.0',             # Simulate 10 seconds
    '--fps', '30',                # Video FPS
    '--slomo', '5',               # 5x slow motion
    '--aoa', '0',                 # Angle of attack 0° (flow along axis)
])

print(f"Velocity: {config.get_float('u')} m/s")
print(f"Reynolds: {config.get_float('re')}")
print(f"STL file: {STL}")
print("Starting simulation... (press P to pause, Esc to quit)")

# Run simulation — opens interactive GPU window!
config.run_simulation()
