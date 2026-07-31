// ============================================================
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
