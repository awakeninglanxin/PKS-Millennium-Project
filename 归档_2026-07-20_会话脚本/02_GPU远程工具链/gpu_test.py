import os, sys, time
sys.path.insert(0, '/root/super_kshape_work')
os.makedirs('/root/super_kshape_results', exist_ok=True)
print("dir ok")

from super_kshape import SuperKShape, generate_synthetic_data
print("import ok")

X, y = generate_synthetic_data(100, 64, 3)
print(f"data: {len(X)} series x {len(X[0])} length")

m = SuperKShape(k=3, max_iter=20)
m.fit(X)
print(f"fit ok, labels shape={m.labels_.shape}")
