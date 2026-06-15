"""
EEQT几何体四元数旋转 - 实时计算版
======================================
直接在JavaScript前端实时计算四元数旋转，无需预计算表
Python端用于生成测试和验证
"""

import math
import json

# ============================================================
# 四元数运算（Python端用于验证）
# ============================================================

def quaternion_mult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return (
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    )

def quaternion_create(axis, angle_deg):
    angle = math.radians(angle_deg)
    ax, ay, az = axis
    norm = math.sqrt(ax*ax + ay*ay + az*az)
    if norm < 1e-10:
        return (1, 0, 0, 0)
    ax, ay, az = ax/norm, ay/norm, az/norm
    half = angle / 2
    return (math.cos(half), ax*math.sin(half), ay*math.sin(half), az*math.sin(half))

def quaternion_inverse(q):
    w, x, y, z = q
    n2 = w*w + x*x + y*y + z*z
    if n2 < 1e-10:
        return (1, 0, 0, 0)
    return (w/n2, -x/n2, -y/n2, -z/n2)

def rotate_point(point, q):
    p = (0, point[0], point[1], point[2])
    q_inv = quaternion_inverse(q)
    temp = quaternion_mult(q, p)
    result = quaternion_mult(temp, q_inv)
    return (result[1], result[2], result[3])

def normalize(v):
    n = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if n < 1e-10:
        return (0, 0, 1)
    return (v[0]/n, v[1]/n, v[2]/n)

# ============================================================
# 生成JavaScript四元数旋转模块
# ============================================================

def generate_js_quaternion_module():
    """生成JavaScript四元数模块代码"""
    
    js_code = '''// ============================================================
// 四元数旋转模块 (自动生成)
// ============================================================

const Quaternion = {
  // 从轴-角创建四元数
  fromAxisAngle: function(axis, angleDeg) {
    const angle = angleDeg * Math.PI / 180;
    const ax = axis[0], ay = axis[1], az = axis[2];
    const norm = Math.sqrt(ax*ax + ay*ay + az*az);
    if(norm < 1e-10) return [1, 0, 0, 0];
    const half = angle / 2;
    const s = Math.sin(half) / norm;
    return [Math.cos(half), ax*s, ay*s, az*s];
  },
  
  // 四元数乘法
  multiply: function(q1, q2) {
    const [w1,x1,y1,z1] = q1;
    const [w2,x2,y2,z2] = q2;
    return [
      w1*w2 - x1*x2 - y1*y2 - z1*z2,
      w1*x2 + x1*w2 + y1*z2 - z1*y2,
      w1*y2 - x1*z2 + y1*w2 + z1*x2,
      w1*z2 + x1*y2 - y1*x2 + z1*w2
    ];
  },
  
  // 四元数共轭
  conjugate: function(q) {
    return [q[0], -q[1], -q[2], -q[3]];
  },
  
  // 四元数逆
  inverse: function(q) {
    const n2 = q[0]*q[0] + q[1]*q[1] + q[2]*q[2] + q[3]*q[3];
    if(n2 < 1e-10) return [1,0,0,0];
    return [q[0]/n2, -q[1]/n2, -q[2]/n2, -q[3]/n2];
  },
  
  // 旋转点
  rotatePoint: function(point, q) {
    const p = [0, point[0], point[1], point[2]];
    const qInv = this.inverse(q);
    const temp = this.multiply(q, p);
    const result = this.multiply(temp, qInv);
    return [result[1], result[2], result[3]];
  },
  
  // 归一化向量
  normalize: function(v) {
    const n = Math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
    if(n < 1e-10) return [0, 0, 1];
    return [v[0]/n, v[1]/n, v[2]/n];
  },
  
  // 组合旋转: 先X，再Y，最后Z
  composeRotation: function(rotX, rotY, rotZ) {
    const qx = this.fromAxisAngle([1,0,0], rotX);
    const qy = this.fromAxisAngle([0,1,0], rotY);
    const qz = this.fromAxisAngle([0,0,1], rotZ);
    const qxy = this.multiply(qy, qx);  // 先X后Y
    return this.multiply(qz, qxy);       // 再Z
  },
  
  // 旋转几何体顶点
  rotateGeometry: function(vertices, rotX, rotY, rotZ) {
    const q = this.composeRotation(rotX, rotY, rotZ);
    return vertices.map(v => {
      const rotated = this.rotatePoint(v, q);
      return this.normalize(rotated);
    });
  }
};
'''
    return js_code

# ============================================================
# 测试验证
# ============================================================

def test_rotation():
    """测试四元数旋转的正确性"""
    print("=" * 60)
    print("四元数旋转测试验证")
    print("=" * 60)
    
    # 测试用例1：Octahedron绕X轴旋转90度
    print("\n【测试1】Octahedron 绕X轴旋转90度:")
    octahedron = [
        [0, 0, 1],
        [1, 0, 0],
        [0, 1, 0],
        [-1, 0, 0],
        [0, -1, 0],
        [0, 0, -1]
    ]
    
    # X轴旋转90度
    qx = quaternion_create((1, 0, 0), 90)
    rotated = [normalize(rotate_point(v, qx)) for v in octahedron]
    
    print("  原始 -> 旋转后:")
    for i in range(len(octahedron)):
        o = octahedron[i]
        r = rotated[i]
        print(f"    {o}  ->  [{r[0]:.6f}, {r[1]:.6f}, {r[2]:.6f}]")
    
    # 验证：绕X轴90度，(0,1,0)应该变成(0,0,1)
    print("\n  验证点(0,1,0)旋转后应为(0,0,1):", rotated[2])
    
    # 测试用例2：绕Y轴旋转90度
    print("\n【测试2】(1,0,0) 绕Y轴旋转90度 应为(0,0,-1):")
    qy = quaternion_create((0, 1, 0), 90)
    result = normalize(rotate_point([1, 0, 0], qy))
    print(f"    结果: [{result[0]:.6f}, {result[1]:.6f}, {result[2]:.6f}]")
    
    # 测试用例3：绕Z轴旋转90度
    print("\n【测试3】(1,0,0) 绕Z轴旋转90度 应为(0,1,0):")
    qz = quaternion_create((0, 0, 1), 90)
    result = normalize(rotate_point([1, 0, 0], qz))
    print(f"    结果: [{result[0]:.6f}, {result[1]:.6f}, {result[2]:.6f}]")
    
    # 测试用例4：组合旋转
    print("\n【测试4】组合旋转: X=90, Y=90, Z=90")
    q = quaternion_create((1, 0, 0), 90)
    q = quaternion_mult(quaternion_create((0, 1, 0), 90), q)
    q = quaternion_mult(quaternion_create((0, 0, 1), 90), q)
    result = normalize(rotate_point([1, 0, 0], q))
    print(f"    (1,0,0) 旋转后: [{result[0]:.6f}, {result[1]:.6f}, {result[2]:.6f}]")
    
    print("\n" + "=" * 60)

def generate_javascript_file():
    """生成JavaScript文件"""
    js_code = generate_js_quaternion_module()
    
    output_path = r"C:\Users\ThinkPad\WorkBuddy\20260425104509\eeqt\quaternion_module.js"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_code)
    
    print(f"JavaScript模块已生成: {output_path}")

if __name__ == "__main__":
    test_rotation()
    generate_javascript_file()
