"""Check { } balance in <script> blocks of an HTML file."""
import sys, re

path = sys.argv[1] if len(sys.argv) > 1 else input("HTML file path: ")
with open(path, encoding='utf-8') as f:
    content = f.read()

scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
if not scripts:
    print("No <script> blocks found.")
    sys.exit(0)

all_ok = True
for i, s in enumerate(scripts):
    opens = s.count('{')
    closes = s.count('}')
    diff = opens - closes
    if diff != 0:
        all_ok = False
        print(f"❌ Block {i}: {opens} {{, {closes} }} (diff={diff})")
        lines = s.split('\n')
        cum = 0
        for j, line in enumerate(lines):
            cum += line.count('{') - line.count('}')
            if abs(cum) > 5:
                print(f"   Near line {j+1} (cum={cum})")
                break
    else:
        print(f"✅ Block {i}: balanced ({opens})")

if all_ok:
    print("All good!")
else:
    sys.exit(1)
