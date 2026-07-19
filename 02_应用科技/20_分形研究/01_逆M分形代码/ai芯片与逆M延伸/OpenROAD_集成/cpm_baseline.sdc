# Hybrid Farey Scheduler — Auto-generated SDC constraints
# Method: FareyTree + InternalAddr hybrid
# Tasks: 8
# Ordered by: complexity <7 → FareyTree depth
#             complexity ≥7 → InternalAddr bifurcation depth

# Rank 1: csr (complexity=2, slack=40ps)
group_path -name csr_grp -weight 8.0 -priority 8
# Rank 2: fetch (complexity=2, slack=20ps)
group_path -name fetch_grp -weight 7.0 -priority 7
# Rank 3: decode (complexity=2, slack=15ps)
group_path -name decode_grp -weight 6.0 -priority 6
# Rank 4: writeback (complexity=2, slack=10ps)
group_path -name writeback_grp -weight 5.0 -priority 5
# Rank 5: execute (complexity=5, slack=-30ps)
group_path -name execute_grp -weight 4.0 -priority 4
# Rank 6: mul_div (complexity=7, slack=-55ps)
group_path -name mul_div_grp -weight 3.0 -priority 3
# Rank 7: memory (complexity=7, slack=-80ps)
group_path -name memory_grp -weight 2.0 -priority 2
# Rank 8: branch (complexity=9, slack=-120ps)
group_path -name branch_grp -weight 1.0 -priority 1