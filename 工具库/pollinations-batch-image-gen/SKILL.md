---
name: pollinations-batch-image-gen
description: Generate images in batch using Pollinations.ai free API for deity weapon art. Use when needing to generate weapon/holder images for Chinese mythological deities in bulk.
agent_created: true
---

# Pollinations Batch Image Generation Skill

Batch-generate weapon/holder images for deity codes using Pollinations.ai free API (no token, no cost).

## When to Use

- User needs to generate 10+ deity weapon images
- ImageGen tool is 429 rate-limited or unavailable
- Need free/cost-free image generation for 1-prefix codes
- Updating deities.js image references en masse

## How to Use

### 1. Edit the batch queue

Edit `scripts/batch_gen_weapons.py` and update the `BATCH2` list with `(code, prompt)` tuples:

```python
BATCH2 = [
    ("1325", "Tang Sanzang holding nine-ring monk staff..."),
]
```

For full automatic scanning (all 1-prefix node images), use the batch3 script approach:

1. Read `deities.js` to find all codes matching `code.startswith('1')` where image contains node keywords
2. Map each node type (Sirius/Orion/Yahyel/etc.) to an appropriate weapon
3. Generate prompts automatically

### 2. Run

```bash
python3 scripts/batch_gen_weapons.py
```

The script:
- Calls `https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux`
- Saves JPG files to `generated-images/`
- Updates `deities.js` image paths automatically
- Waits 5-8 seconds between images to avoid rate limiting

### 3. Verify

```bash
# Check how many 1-prefix codes still have node images
python3 -c "
import re
with open('deities.js') as f: js=f.read()
entries = re.findall(r'code:\"(\\d+)\".*?image:\"([^\"]+)\"', js)
node_keywords = ['Grey_','Essassani_','Sirius_','Orion_','Yahyel_','Pleiades_','Annunaki_','Gaia_','Arcturus_','Acquired_','Four_Pure_','Sanqing_','Duodecimal_','Innate_Child_']
remaining = [(c,img) for c,img in entries if c.startswith('1') and any(k in img for k in node_keywords)]
print(f'Remaining node images: {len(remaining)}')
"
```

## Performance

- ~1 image per 30 seconds (15-20s generation + 8s delay)
- 100 images ≈ 50 minutes
- JPG output, ~80-150KB each
- 1024x1024 resolution, Flux model
