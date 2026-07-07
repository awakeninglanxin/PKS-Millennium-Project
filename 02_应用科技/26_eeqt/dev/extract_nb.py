import re

with open('C:/Users/ThinkPad/.openclaw/workspace/eeqt/Demonstration-Quantum-Octahedral-Fractal-via-Random-Spin-State-Jumps-1-0-0-definition.nb', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Look for the key parameters
patterns = [
    (r'k_.*?:=', 'Function definition'),
    (r'RandomInteger.*?\[', 'Random'),
    (r'PointSize.*?\]', 'PointSize'),
    (r'PlotStyle.*?\]', 'PlotStyle'),
    (r'ColorFunction.*?\]', 'ColorFunction'),
    (r'PoincareDisk', 'PoincareDisk'),
    (r'Stereographic', 'Stereographic'),
    (r'VectorColorFunction', 'VectorColorFunction'),
    (r'VectorStyle', 'VectorStyle'),
]

# Find all occurrences of key patterns
for pat, name in patterns:
    matches = re.findall(pat, content)
    if matches:
        print(f"\n=== {name} ===")
        for m in matches[:5]:
            print(f"  {m[:200]}")

# Find the core iteration function
if 'f[' in content or 'f$' in content:
    idx = content.find('f[')
    if idx > 0:
        print(f"\n=== Context around f[ ===")
        print(content[max(0,idx-200):idx+500])
