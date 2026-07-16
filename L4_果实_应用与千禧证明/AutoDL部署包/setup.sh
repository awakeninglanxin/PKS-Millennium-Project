#!/bin/bash
echo "=== AutoDL PKS 环境部署 ==="
pip install cupy-cuda12x matplotlib numpy scipy --quiet
echo "=== 环境就绪 ==="
python -c "import cupy; print(f'GPU: {cupy.cuda.runtime.getDeviceCount()} devices, {cupy.cuda.runtime.getDeviceProperties(0)[\"name\"].decode()}')"
echo "=== 运行 BSD v2: 6曲线 rank 0-3 验证 ==="
python BSD_v2_DerivativeKernel.py
