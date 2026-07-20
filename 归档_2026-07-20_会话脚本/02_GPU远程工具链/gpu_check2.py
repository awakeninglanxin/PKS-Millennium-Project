import os, sys, traceback
sys.path.insert(0, '/root/super_kshape_work')

try:
    os.makedirs('/root/super_kshape_results', exist_ok=True)
    print("step1: dir ok", flush=True)
    
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    print("step2: matplotlib ok", flush=True)
    
    import seaborn as sns
    print(f"step3: seaborn {sns.__version__}", flush=True)
    
    from super_kshape import SuperKShape, generate_synthetic_data
    print("step4: imports ok", flush=True)
    
    print(f"checking gpu_dashboard.py existence...")
    with open('/root/super_kshape_work/gpu_dashboard.py') as f:
        lines = f.readlines()
    print(f"gpu_dashboard.py: {len(lines)} lines, starts with: {lines[0].strip()}")
    
except Exception as e:
    traceback.print_exc()
