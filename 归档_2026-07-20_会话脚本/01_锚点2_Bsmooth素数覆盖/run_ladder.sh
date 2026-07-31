cd /root/smooth_work
: > summary.jsonl
echo "=== ladder start $(date) ==="
python3 smooth_gpu.py --k 7  --X 1e8 --D 1e11
python3 smooth_gpu.py --k 8  --X 1e8 --D 1e12
python3 smooth_gpu.py --k 9  --X 1e8 --D 1e12
python3 smooth_gpu.py --k 10 --X 1e8 --D 1e12
python3 smooth_gpu.py --k 9  --X 1e7 --D 1e13
python3 smooth_gpu.py --k 9  --X 1e9 --D 1e12
python3 smooth_gpu.py --k 10 --X 1e9 --D 1e12
python3 smooth_gpu.py --k 11 --X 1e9 --D 1e12
echo "=== LADDER_DONE $(date) ==="
