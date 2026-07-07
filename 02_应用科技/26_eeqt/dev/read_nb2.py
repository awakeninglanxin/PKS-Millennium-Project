import re

with open('C:/Users/ThinkPad/.openclaw/workspace/eeqt/Demonstration-Quantum-Octahedral-Fractal-via-Random-Spin-State-Jumps-1-0-0-definition.nb', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find all Cell expressions with BoxData (these are input cells)
# Look for the actual function definitions
cells = content.split('Cell[')

print(f"Total cells: {len(cells)}")
print()

# Look for cells containing function definitions or NestList
for i, cell in enumerate(cells):
    if 'NestList' in cell and 'f[' in cell:
        # Extract the BoxData content
        boxdata = re.findall(r'BoxData\[(.*?)\], "Input"', cell, re.DOTALL)
        if boxdata:
            text = boxdata[0]
            # Clean up Mathematica box language
            # Remove StyleBox wrappers
            text = re.sub(r'StyleBox\[(.*?),.*?\]', r'\1', text)
            text = re.sub(r'RowBox\[(.*?)\]', lambda m: m.group(1), text)
            # Remove quotes
            text = text.replace('"', ' ').replace("'", ' ')
            if len(text) > 0 and len(text) < 2000:
                print(f"Cell {i}:")
                print(text[:1500])
                print("---")
