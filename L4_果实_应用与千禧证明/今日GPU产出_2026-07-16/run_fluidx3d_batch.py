"""FluidX3D 批量 CFD — 6种漏斗 STL 对比 (无图形，纯数据导出)"""
import fluidx3d, os, glob

STL_DIR = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\05_参考资料\几种漏斗stl文件"
STL_FILES = sorted(glob.glob(os.path.join(STL_DIR, "*.stl")))

for stl_path in STL_FILES:
    name = os.path.basename(stl_path).replace('.stl', '')
    sz_kb = os.path.getsize(stl_path) // 1024
    print(f"\n{'='*60}\n{name} ({sz_kb}KB)\n{'='*60}")
    
    config = fluidx3d.Config()
    config.parse_args([
        '--D3Q27', '--FP16S', '--SRT',
        '--EQUILIBRIUM_BOUNDARIES', '--UPDATE_FIELDS',
        '-f', stl_path,
        '-r', '2000',          # 2GB VRAM
        '-u', '3.0',           # 3 m/s
        '--re', '150',         # Re=150
        '--rho', '1000',       # water
        '--secs', '5.0',       # 5 seconds each
        '--export', f'./output_{name}/',
    ])
    
    try:
        config.run_simulation()
        print(f"  ✅ {name} completed")
    except Exception as ex:
        print(f"  ❌ {name} FAILED: {ex}")

print("\n🎉 All 6 STL simulations submitted!")
