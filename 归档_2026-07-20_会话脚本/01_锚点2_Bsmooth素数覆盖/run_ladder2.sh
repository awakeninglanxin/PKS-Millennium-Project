cd /root/smooth_work
echo "=== ladder2 start $(date) ==="
echo "--- k=12 X=1e8 (predict 0 miss, X*~5e8) ---"
python3 smooth_gpu.py --k 12 --X 1e8 --D 1e11
echo "--- k=12 X=1e9 (predict first miss ~5e8-1e9) ---"
python3 smooth_gpu.py --k 12 --X 1e9 --D 1e11
echo "--- k=13 X=1e9 (predict 0 miss, X*~3e10 >> 1e9) ---"
python3 smooth_gpu.py --k 13 --X 1e9 --D 5e10
echo "--- deep_check k9 X1e8 (first 40 + last 10) ---"
python3 deep_check_remote.py k9_X1e08
echo "--- deep_check k10 X1e8 (first 40 + last 10) ---"
python3 deep_check_remote.py k10_X1e08
echo "=== LADDER2_DONE $(date) ==="
