import re

with open('C:/Users/ThinkPad/.openclaw/workspace/eeqt/Demonstration-Quantum-Octahedral-Fractal-via-Random-Spin-State-Jumps-1-0-0-definition.nb', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

lines = content.split('\n')
keywords = ['k', 'Poincare', 'Sphere', 'Plot', 'Graphics3D', 'Point', 'ColorFunction', 'Spin', 'Random', 'Moebius', 'Mobius', '混沌', 'iteration', 'chaos']

results = []
for i, line in enumerate(lines):
    for kw in keywords:
        if kw in line and len(line.strip()) > 15:
            results.append(f'{i}: {line[:300]}')
            break

with open('C:/Users/ThinkPad/.openclaw/workspace/eeqt/fragments.txt', 'w', encoding='utf-8') as out:
    out.write('\n'.join(results))

print(f"Found {len(results)} lines")
print("Written to fragments.txt")
