cd /root/inverse_m_work

echo "############ 1) SEAHORSE 高清 (c=-0.74543+0.11301j) ############"
python3 inverse_m_tree.py --c=-0.74543+0.11301j --depth 16 --gpu --npoints 8000000 --nsteps 200

echo "############ 2) c=-1 dragon ############"
python3 inverse_m_tree.py --c=-1.0+0.0j --depth 12 --gpu --npoints 3000000 --nsteps 140

echo "############ 3) c=i spiral/dendrite ############"
python3 inverse_m_tree.py --c=0.0+1.0j --depth 12 --gpu --npoints 3000000 --nsteps 140

echo "############ 4) c=0 unit circle ############"
python3 inverse_m_tree.py --c=0.0+0.0j --depth 12 --gpu --npoints 3000000 --nsteps 140

echo "############ 5) c=-0.8+0.156j rabbit ############"
python3 inverse_m_tree.py --c=-0.8+0.156j --depth 12 --gpu --npoints 3000000 --nsteps 140

echo "ALL DONE"
ls -la /root/inverse_m_work
