# 音乐谐波算法（Fibonacci/Phi倍频）

**目录**: `D:\AAA我的文件\PKS_千禧难题_统一解\01_基础理论\26_音乐谐波`
**文件数**: 9 个 .py 文件

---

## 文件说明与参数详解

### 📄 fibonacci+2的倍频谐波的音乐 castle_in_the_sky.py

**功能描述**: 根据音符名称和八度计算频率 # A4是第9个音符，在八度4 A4_note = 9 A4_octave = 4 # 计算相对于A4的半音偏移 semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12 # 计算频率 return A4_freq * (2 ** (semitone_offse...

**依赖**:
- `import numpy as np`
- `from scipy.io import wavfile`
- `import math`
- `import traceback`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 0.6 | 基本参数 | (见源码注释) |
| `k` | 0.1 | 基本参数 | (见源码注释) |
| `freq` | 432.0 | 几何参数 | (见源码注释) |
| `amplitude` | 1.0 | 几何参数 | (见源码注释) |

**关键数学逻辑**:

```python
semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12
linear_factor = 1.0 - (abs(k) / harmonic_range) * 0.7
attack_samples = int(attack * sample_rate)
decay_samples = int(decay * sample_rate)
release_samples = int(release * sample_rate)
```

**函数流程**:
- `get_frequency_from_note()`
- `linear_decay_amplitude()`
- `fibonacci_exp_decay_amplitude()`
- `adsr_envelope()`
- `generate_note_with_dual_harmonics()`
- `create_castle_in_the_sky()`
- `save_audio_to_wav()`
- `print_music_info()`
- `main()`

---

### 📄 fibonacci+2的倍频谐波的音乐 天空之城.py

**功能描述**: 根据音符名称和八度计算频率 # A4是第9个音符，在八度4 A4_note = 9 A4_octave = 4 # 计算相对于A4的半音偏移 semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12 # 计算频率 return A4_freq * (2 ** (semitone_offse...

**依赖**:
- `import numpy as np`
- `from scipy.io import wavfile`
- `import math`
- `import traceback`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 0.5 | 基本参数 | (见源码注释) |
| `k` | 0.1 | 基本参数 | (见源码注释) |
| `freq` | 432.0 | 几何参数 | (见源码注释) |
| `amplitude` | 1.0 | 几何参数 | (见源码注释) |

**关键数学逻辑**:

```python
semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12
linear_factor = 1.0 - (abs(k) / harmonic_range) * 0.7
attack_samples = int(attack * sample_rate)
decay_samples = int(decay * sample_rate)
release_samples = int(release * sample_rate)
```

**函数流程**:
- `get_frequency_from_note()`
- `linear_decay_amplitude()`
- `fibonacci_exp_decay_amplitude()`
- `adsr_envelope()`
- `generate_note_with_dual_harmonics()`
- `create_castle_in_the_sky()`
- `save_audio_to_wav()`
- `print_music_info()`
- `main()`

---

### 📄 fibonacci数列音乐+2的倍频谐波.py

**功能描述**: 生成Fibonacci数列 fibonacci = [1, 1] for i in range(2, count): fibonacci.append(fibonacci[i - 1] + fibonacci[i - 2]) return fibonacci def calculate_frequency_from_semitone(semitone_offset, A4_freq=432.0):...

**依赖**:
- `import numpy as np`
- `from scipy.io import wavfile`
- `import math`
- `import traceback`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 1.45 | 基本参数 | (见源码注释) |
| `k` | 0.02 | 基本参数 | (见源码注释) |
| `freq` | 432.0 | 几何参数 | (见源码注释) |
| `amplitude` | 1.0 | 几何参数 | (见源码注释) |

**关键数学逻辑**:

```python
note_duration = 1.45 / 2  # 每个音符1.45秒/2
A0_freq = A4_freq / 16
attack_samples = int(attack * sample_rate)
decay_samples = int(decay * sample_rate)
release_samples = int(release * sample_rate)
```

**函数流程**:
- `generate_fibonacci_sequence()`
- `calculate_frequency_from_semitone()`
- `adsr_envelope()`
- `linear_decay_amplitude()`
- `fibonacci_exp_decay_amplitude()`
- `generate_note_with_dual_harmonics()`
- `create_fibonacci_music_with_dual_harmonics()`
- `save_audio_to_wav()`
- `print_harmonic_info()`
- `main()`

---

### 📄 fibonacci音乐+2的倍频谐波 波振幅衰减示意图.py

**功能描述**: 弹簧式指数衰减振幅计算 参数: k: 谐波序号，0表示基频，正数表示倍频，负数表示分频 k_factor: 衰减因子，控制衰减速度 base_amplitude: 基频振幅 演示弹簧衰减算法 # 测试不同的衰减因子 k_factors = [0.3, 0.7, 1.2, 2.0] k_values = list(range(-4, 5))  # k从-4到4 plt.figure(figsize=...

**依赖**:
- `import math`
- `import matplotlib.pyplot as plt`
- `import numpy as np`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `a` | 0.3 | 基本参数 | (见源码注释) |
| `k` | 0 | 基本参数 | (见源码注释) |
| `amplitude` | 1.0 | 几何参数 | (见源码注释) |
| `freq` | 440 | 几何参数 | (见源码注释) |
| `alpha` | 0.3 | 权重/阈值 | (见源码注释) |

**关键数学逻辑**:

```python
k_values = list(range(-4, 5))  # k从-4到4
freq = base_freq * freq_ratio
f"  k_factor={k_factor}: 振幅 = {amp:.4f} (衰减到基波的 {amp / spring_decay_amplitude(0, k_factor):.2%})")
amp_ratio = spring_decay_amplitude(k, 1.0) / spring_decay_amplitude(0, 1.0)
linear_amp = 1.0 / (1 + k)  # 线性衰减
```

**函数流程**:
- `spring_decay_amplitude()`
- `demonstrate_spring_decay()`
- `calculate_frequency_ratio()`
- `analyze_harmonic_relationships()`
- `mathematical_analysis()`
- `compare_decay_patterns()`

---

### 📄 phi值+2的倍频谐波的音乐 天空之城 -ai纯音 高品质钢琴 纯音.py

**功能描述**: 根据音符名称和八度计算频率 A4_note = 9 A4_octave = 4 semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12 return A4_freq * (2 ** (semitone_offset / 12)) def piano_like_octave_decay(k...

**依赖**:
- `import numpy as np`
- `from scipy.io import wavfile`
- `import math`
- `import traceback`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 0.5 | 基本参数 | (见源码注释) |
| `freq` | 432.01 | 几何参数 | (见源码注释) |
| `amplitude` | 1.0 | 几何参数 | (见源码注释) |

**关键数学逻辑**:

```python
semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12
decay_time = min(0.3, duration * 0.3)
release_time = min(0.5, duration * 0.5)
attack_samples = int(attack_time * sample_rate)
decay_samples = int(decay_time * sample_rate)
```

**函数流程**:
- `get_frequency_from_note()`
- `piano_like_octave_decay()`
- `piano_like_fibonacci_decay()`
- `piano_adsr_envelope()`
- `generate_pure_piano_note()`
- `create_pure_piano_castle_in_the_sky()`
- `save_audio_to_wav()`
- `main()`

---

### 📄 phi值+2的倍频谐波的音乐 天空之城 -ai纯音 高品质钢琴 轻微失谐.py

**功能描述**: 根据音符名称和八度计算频率 A4_note = 9 A4_octave = 4 semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12 return A4_freq * (2 ** (semitone_offset / 12)) def piano_like_octave_decay(k...

**依赖**:
- `import numpy as np`
- `from scipy.io import wavfile`
- `import math`
- `import traceback`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 0.5 | 基本参数 | (见源码注释) |
| `freq` | 432.01 | 几何参数 | (见源码注释) |
| `amplitude` | 1.0 | 几何参数 | (见源码注释) |

**关键数学逻辑**:

```python
semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12
decay_time = min(0.3, duration * 0.3)  # 衰减时间与音符时长相关
release_time = min(0.5, duration * 0.5)  # 释音时间
attack_samples = int(attack_time * sample_rate)
decay_samples = int(decay_time * sample_rate)
```

**函数流程**:
- `get_frequency_from_note()`
- `piano_like_octave_decay()`
- `piano_like_fibonacci_decay()`
- `piano_adsr_envelope()`
- `generate_piano_like_note()`
- `create_piano_like_castle_in_the_sky()`
- `save_audio_to_wav()`
- `analyze_piano_characteristics()`
- `main()`

---

### 📄 phi值+2的倍频谐波的音乐 天空之城 -ai纯音.py

**功能描述**: 根据音符名称和八度计算频率 A4_note = 9 A4_octave = 4 semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12 return A4_freq * (2 ** (semitone_offset / 12)) def improved_linear_decay_amp...

**依赖**:
- `import numpy as np`
- `from scipy.io import wavfile`
- `import math`
- `import traceback`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 0.5 | 基本参数 | (见源码注释) |
| `k` | 0.08 | 基本参数 | (见源码注释) |
| `freq` | 432.0 | 几何参数 | (见源码注释) |
| `amplitude` | 1.0 | 几何参数 | (见源码注释) |

**关键数学逻辑**:

```python
semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12
distance_factor = abs(k) / harmonic_range
linear_factor = 1.0 - (distance_factor ** 0.7) * 0.8  # 更平缓的衰减
exp_decay = math.exp(-abs(harmonic_num) * k_factor)
fib_enhancement = 1.0 + fib_enhance
```

**函数流程**:
- `get_frequency_from_note()`
- `improved_linear_decay_amplitude()`
- `improved_fibonacci_decay_amplitude()`
- `natural_adsr_envelope()`
- `generate_note_with_improved_harmonics()`
- `create_improved_castle_in_the_sky()`
- `save_audio_to_wav()`
- `analyze_harmonic_structure()`
- `main()`

---

### 📄 phi值+2的倍频谐波的音乐 天空之城 -ai颤音.py

**功能描述**: 根据音符名称和八度计算频率 A4_note = 9 A4_octave = 4 semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12 return A4_freq * (2 ** (semitone_offset / 12)) def improved_linear_decay_amp...

**依赖**:
- `import numpy as np`
- `from scipy.io import wavfile`
- `import math`
- `import traceback`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 0.5 | 基本参数 | (见源码注释) |
| `k` | 0.08 | 基本参数 | (见源码注释) |
| `freq` | 432.0 | 几何参数 | (见源码注释) |
| `amplitude` | 1.0 | 几何参数 | (见源码注释) |

**关键数学逻辑**:

```python
semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12
distance_factor = abs(k) / harmonic_range
linear_factor = 1.0 - (distance_factor ** 0.7) * 0.8  # 更平缓的衰减
exp_decay = math.exp(-abs(harmonic_num) * k_factor)
fib_enhancement = 1.0 + fib_enhance
```

**函数流程**:
- `get_frequency_from_note()`
- `improved_linear_decay_amplitude()`
- `improved_fibonacci_decay_amplitude()`
- `natural_adsr_envelope()`
- `generate_note_with_improved_harmonics()`
- `create_improved_castle_in_the_sky()`
- `save_audio_to_wav()`
- `analyze_harmonic_structure()`
- `main()`

---

### 📄 黄金比音乐+2的倍频谐波.py

**功能描述**: 生成Fibonacci数列 fibonacci = [1, 1] for i in range(2, count): fibonacci.append(fibonacci[i - 1] + fibonacci[i - 2]) return fibonacci def calculate_frequency_from_semitone(semitone_offset, A4_freq=432.0):...

**依赖**:
- `import numpy as np`
- `from scipy.io import wavfile`
- `import math`
- `import traceback`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 1.45 | 基本参数 | (见源码注释) |
| `k` | 0.02 | 基本参数 | (见源码注释) |
| `m` | 89 | 基本参数 | (见源码注释) |
| `freq` | 432.0 | 几何参数 | (见源码注释) |
| `amplitude` | 1.0 | 几何参数 | (见源码注释) |

**关键数学逻辑**:

```python
note_duration = 1.45 / 2  # 每个音符1.45秒/2
A0_freq = A4_freq / 16
attack_samples = int(attack * sample_rate)
decay_samples = int(decay * sample_rate)
release_samples = int(release * sample_rate)
```

**函数流程**:
- `generate_fibonacci_sequence()`
- `calculate_frequency_from_semitone()`
- `adsr_envelope()`
- `linear_decay_amplitude()`
- `fibonacci_exp_decay_amplitude()`
- `generate_note_with_dual_harmonics()`
- `create_fibonacci_music_with_dual_harmonics()`
- `save_audio_to_wav()`
- `print_harmonic_info()`
- `test_decay_functions()`

---

## 使用说明

### 运行环境

- 大部分文件需 **Rhino 3D**（`import rhinoscriptsyntax`）
- 少数文件可在标准 Python 环境运行（`matplotlib`/`numpy`）
- 音乐算法文件需 `pygame` 或 `pyaudio` 播放 MIDI

### 参数调节原则

1. **几何参数**（`k`, `b`, `a`, `m`）— 控制曲线形状
2. **缩放参数**（`scale`, `amplitude`, `n`）— 控制幅度/圈数
3. **权重参数**（`weight`, `alpha`, `beta`）— 控制混合比例

### 输出

- Rhino 脚本：直接在 Rhino 视口中生成曲线/曲面
- matplotlib 脚本：输出 `.png` 可视化文件
- 音乐算法：播放音频或输出 MIDI

---

*本说明由 AI 自动生成于 2026-06-15 19:51*