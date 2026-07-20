#!/usr/bin/env node
/**
 * Auto File Splitter - 一键检查并自动拆分
 * 检查目录下所有py/js文件，自动拆分超过19KB的文件
 * 输出目录格式: 原文件名_module/
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const MAX_SIZE = 19 * 1024; // 19KB
const MAX_SIZE_KB = 19;

class AutoFileSplitter {
  constructor(targetDir = '.') {
    this.targetDir = targetDir;
    this.results = {
      scanned: 0,
      oversized: [],
      split: [],
      skipped: [],
      errors: []
    };
  }

  /**
   * 一键执行：扫描 + 拆分
   */
  run() {
    console.log('\n============================================================');
    console.log('🔍 一键文件拆分检查器');
    console.log('============================================================');
    console.log(`📁 扫描目录: ${path.resolve(this.targetDir)}`);
    console.log(`📏 大小限制: ${MAX_SIZE_KB}KB`);
    console.log('============================================================\n');

    // Step 1: 扫描文件
    const files = this.scanFiles();
    
    // Step 2: 找出超限文件
    const oversizedFiles = this.findOversizedFiles(files);
    
    // Step 3: 自动拆分
    if (oversizedFiles.length > 0) {
      console.log('\n🔄 开始自动拆分...\n');
      this.autoSplit(oversizedFiles);
    } else {
      console.log('✅ 所有文件均满足大小限制，无需拆分！\n');
    }

    // Step 4: 生成报告
    this.printReport();

    // Step 5: 更新 CODE_INDEX.md
    this.updateIndex();
    
    return this.results;
  }

  /**
   * 扫描目录下的py/js文件
   */
  scanFiles() {
    console.log('📂 扫描文件中...');
    const files = [];
    
    const extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.vue'];
    
    this.scanDirectory(this.targetDir, extensions, files);
    
    console.log(`   发现 ${files.length} 个目标文件\n`);
    return files;
  }

  /**
   * 递归扫描目录
   */
  scanDirectory(dir, extensions, files, excludeDirs = ['node_modules', '__pycache__', '.git', 'modules', 'node_modules']) {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory()) {
          // 排除特定目录
          if (!excludeDirs.includes(entry.name) && !entry.name.endsWith('_module')) {
            this.scanDirectory(fullPath, extensions, files, excludeDirs);
          }
        } else if (entry.isFile()) {
          const ext = path.extname(entry.name).toLowerCase();
          if (extensions.includes(ext)) {
            files.push(fullPath);
          }
        }
      }
    } catch (err) {
      // 忽略无法访问的目录
    }
  }

  /**
   * 找出超过限制的文件
   */
  findOversizedFiles(files) {
    console.log('📊 检查文件大小...\n');
    console.log('   ' + '─'.repeat(60));
    console.log(`   ${'文件名'.padEnd(40)} ${'大小'.padStart(10)} ${'状态'}`);
    console.log('   ' + '─'.repeat(60));
    
    const oversized = [];
    
    for (const file of files) {
      this.results.scanned++;
      const stats = fs.statSync(file);
      const sizeKB = (stats.size / 1024).toFixed(1);
      const relativePath = path.relative(process.cwd(), file);
      
      if (stats.size > MAX_SIZE) {
        oversized.push(file);
        this.results.oversized.push({ file, size: stats.size, sizeKB });
        console.log(`   ${relativePath.padEnd(40)} ${(sizeKB + 'KB').padStart(10)} ⚠️ 超限`);
      } else {
        console.log(`   ${relativePath.padEnd(40)} ${(sizeKB + 'KB').padStart(10)} ✅ 正常`);
      }
    }
    
    console.log('   ' + '─'.repeat(60));
    console.log(`   超限文件: ${oversized.length} 个\n`);
    
    return oversized;
  }

  /**
   * 自动拆分超限文件
   */
  autoSplit(oversizedFiles) {
    for (const file of oversizedFiles) {
      console.log(`\n📦 处理: ${path.basename(file)}`);
      
      try {
        const ext = path.extname(file).toLowerCase();
        const baseName = path.basename(file, ext);
        const dirName = path.dirname(file);
        const moduleDir = path.join(dirName, `${baseName}_module`);
        
        // 创建模块目录
        if (!fs.existsSync(moduleDir)) {
          fs.mkdirSync(moduleDir, { recursive: true });
        }
        
        // 备份原文件（带时间戳）
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const backupPath = `${file}.${timestamp}.backup`;
        fs.copyFileSync(file, backupPath);
        console.log(`   📋 备份已创建`);

        // 调用对应的splitter（已备份，跳过splitter内部备份）
        if (['.js', '.jsx', '.ts', '.tsx', '.vue'].includes(ext)) {
          this.splitJSFile(file, moduleDir, true); // skipBackup=true
        } else if (ext === '.py') {
          this.splitPYFile(file, moduleDir);
        }
        
        this.results.split.push({ file, moduleDir });
        console.log(`   ✅ 拆分完成 → ${baseName}_module/`);
        
      } catch (err) {
        console.log(`   ❌ 拆分失败: ${err.message}`);
        this.results.errors.push({ file, error: err.message });
      }
    }
  }

  /**
   * 拆分JS文件
   */
  splitJSFile(file, moduleDir, skipBackup = false) {
    const splitterPath = 'c:\\Users\\ThinkPad\\.workbuddy\\skills\\js-file-splitter\\scripts\\smart_split.js';
    const skipFlag = skipBackup ? '--skipBackup' : '';

    try {
      const cmd = `node "${splitterPath}" "${file}" "${path.basename(moduleDir)}" ${skipFlag}`.trim();
      const result = execSync(cmd, {
        cwd: path.dirname(file),
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe']
      });
      console.log(result);
    } catch (err) {
      // splitter可能在Windows输出有问题，尝试其他方式
      console.log('   (使用简化拆分模式)');
      this.simpleSplitJS(file, moduleDir);
    }
  }

  /**
   * 简化JS拆分
   */
  simpleSplitJS(file, moduleDir) {
    const code = fs.readFileSync(file, 'utf-8');
    const analysis = this.analyzeJS(code);
    
    let fileIndex = 0;
    
    // 生成每个函数/类
    analysis.functions.forEach(fn => {
      const fnFile = path.join(moduleDir, `${this.toKebabCase(fn.name)}.js`);
      const content = `${fn.code}\n`;
      fs.writeFileSync(fnFile, content, 'utf-8');
      fileIndex++;
    });
    
    analysis.classes.forEach(cls => {
      const clsFile = path.join(moduleDir, `${this.toKebabCase(cls.name)}.js`);
      const content = `${cls.code}\n`;
      fs.writeFileSync(clsFile, content, 'utf-8');
      fileIndex++;
    });
    
    // 生成主文件
    this.generateJSEntry(file, moduleDir, analysis);
    
    console.log(`   📄 生成了 ${fileIndex} 个模块文件`);
  }

  /**
   * 拆分Python文件
   */
  splitPYFile(file, moduleDir) {
    const splitterPath = 'c:\\Users\\ThinkPad\\.workbuddy\\skills\\python-file-splitter\\scripts\\smart_split.py';
    
    try {
      const result = execSync(`python "${splitterPath}" "${file}" "${path.basename(moduleDir)}"`, {
        cwd: path.dirname(file),
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe']
      });
      console.log(result);
    } catch (err) {
      console.log('   (使用简化拆分模式)');
      this.simpleSplitPY(file, moduleDir);
    }
  }

  /**
   * 简化Python拆分
   */
  simpleSplitPY(file, moduleDir) {
    const code = fs.readFileSync(file, 'utf-8');
    const analysis = this.analyzePY(code);
    
    let fileIndex = 0;
    
    // 生成每个函数/类
    analysis.functions.forEach(fn => {
      const fnFile = path.join(moduleDir, `${fn.name}.py`);
      const content = `${fn.code}\n`;
      fs.writeFileSync(fnFile, content, 'utf-8');
      fileIndex++;
    });
    
    analysis.classes.forEach(cls => {
      const clsFile = path.join(moduleDir, `${cls.name}.py`);
      const content = `${cls.code}\n`;
      fs.writeFileSync(clsFile, content, 'utf-8');
      fileIndex++;
    });
    
    // 生成主文件
    this.generatePYEntry(file, moduleDir, analysis);
    
    console.log(`   📄 生成了 ${fileIndex} 个模块文件`);
  }

  /**
   * 分析JS代码
   */
  analyzeJS(code) {
    const analysis = { functions: [], classes: [] };
    
    // 提取函数
    const funcRegex = /^(export\s+)?(async\s+)?function\s+(\w+)\s*\([\s\S]*?\n^}/gm;
    let match;
    while ((match = funcRegex.exec(code)) !== null) {
      analysis.functions.push({
        name: match[3],
        code: match[0]
      });
    }
    
    // 提取箭头函数
    const arrowRegex = /^(export\s+)?const\s+(\w+)\s*=\s*(async\s*)?\([\s\S]*?\n^}/gm;
    while ((match = arrowRegex.exec(code)) !== null) {
      analysis.functions.push({
        name: match[2],
        code: match[0]
      });
    }
    
    // 提取类
    const classRegex = /^(export\s+)?class\s+(\w+)[\s\S]*?\n^}/gm;
    while ((match = classRegex.exec(code)) !== null) {
      analysis.classes.push({
        name: match[2],
        code: match[0]
      });
    }
    
    return analysis;
  }

  /**
   * 分析Python代码
   */
  analyzePY(code) {
    const analysis = { functions: [], classes: [] };
    
    // 提取函数
    const funcRegex = /^(def|async\s+def)\s+(\w+)\s*\([\s\S]*?\n(?=\n[A-Za-z_]|\Z)/gm;
    let match;
    while ((match = funcRegex.exec(code)) !== null) {
      analysis.functions.push({
        name: match[2],
        code: match[0]
      });
    }
    
    // 提取类
    const classRegex = /^class\s+(\w+)[\s\S]*?(?=\nclass\s|\ndef\s|\Z)/gm;
    while ((match = classRegex.exec(code)) !== null) {
      analysis.classes.push({
        name: match[1],
        code: match[0]
      });
    }
    
    return analysis;
  }

  /**
   * 提取Python源文件中的 if __name__ == "__main__": 代码块内容
   */
  extractPYMainBlock(sourceCode) {
    // 使用逐行缩进追踪，能正确处理深层嵌套（函数内定义函数、多级try/except等）
    const lines = sourceCode.split('\r\n');
    let inMain = false;
    let baseIndent = -1;
    let mainLines = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      if (!inMain) {
        if (/^if\\s+__name__\\s*==\\s*["']__main__["']\\s*:/.test(trimmed)) {
          inMain = true;
          baseIndent = line.length - line.trimStart().length;
          continue;
        }
      } else {
        if (trimmed === '') { mainLines.push(''); continue; }
        const currentIndent = line.length - line.trimStart().length;
        if (currentIndent <= baseIndent && trimmed && !trimmed.startsWith('#')) break;
        const relativeIndent = Math.max(0, currentIndent - baseIndent - 4);
        mainLines.push(' '.repeat(relativeIndent) + trimmed);
      }
    }

    return mainLines.join('\r\n').trimEnd();
  }

  /**
   * 提取JS源文件中的可执行代码块
   */
  extractJSMainBlock(sourceCode) {
    const lines = sourceCode.split('\n');
    let executableLines = [];
    let inBlock = false;
    let depth = 0;

    for (const line of lines) {
      const trimmed = line.trim();

      if (!inBlock) {
        // 模式: if (require.main === module) {
        if (/if\s*\(\s*require\.main\s*===\s*module\s*\)\s*\{/.test(trimmed)) {
          inBlock = true;
          depth = 1;
          continue;
        }
        // 模式: 顶层调用
        if (/^[a-zA-Z_$][a-zA-Z0-9_$]*\s*\(/.test(trimmed) && trimmed.endsWith(');') &&
            !trimmed.startsWith('function') && !trimmed.startsWith('const ') &&
            !trimmed.startsWith('let ') && !trimmed.startsWith('var ') &&
            !trimmed.startsWith('import ') && !trimmed.startsWith('export ')) {
          executableLines.push(line);
        }
      } else {
        executableLines.push(line);
        const opens = (line.match(/\{/g) || []).length;
        const closes = (line.match(/\}/g) || []).length;
        depth += opens - closes;
        if (depth <= 0) {
          inBlock = false;
          // 去掉最后的闭合大括号
          if (executableLines.length > 0 && executableLines[executableLines.length - 1].trim() === '}') {
            executableLines.pop();
          }
        }
      }
    }

    return executableLines.join('\n').trim();
  }

  /**
   * 生成JS入口文件 - 写入模块目录内，不覆盖原文件
   */
  generateJSEntry(originalFile, moduleDir, analysis) {
    const baseName = path.basename(originalFile, path.extname(originalFile));
    const entries = [
      ...analysis.functions.map(f => f.name),
      ...analysis.classes.map(c => c.name)
    ];

    // 读取原文件，提取可执行代码
    const originalSource = fs.readFileSync(originalFile, 'utf-8');
    const executableBlock = this.extractJSMainBlock(originalSource);

    // 主入口文件放在模块目录内（不覆盖原文件！）
    const mainPath = path.join(moduleDir, `${baseName}_main.js`);
    
    const imports = entries.map(name => 
      `import { ${name} } from './${path.basename(moduleDir)}/${this.toKebabCase(name)}.js';`
    );
    
    let content = [
      '// Auto-generated entry file',
      `// Source: ${path.basename(originalFile)}`,
      '// Generated by auto-file-splitter',
      '',
      ...imports,
      '',
      'export {',
      ...entries.map(e => `  ${e}`),
      '};'
    ].join('\n');
    
    // 追加可执行代码块
    if (executableBlock) {
      content += '\n\n' +
        '// === 原文件可执行代码（自动提取）===\n' +
        executableBlock + '\n';
    }
    
    fs.writeFileSync(mainPath, content, 'utf-8');
    console.log(`   ✅ 生成JS主入口: ${path.basename(mainPath)} (含可执行代码)`);
  }

  /**
   * 生成Python入口文件 - 写入模块目录内，不覆盖原文件
   */
  generatePYEntry(originalFile, moduleDir, analysis) {
    const baseName = path.basename(originalFile, path.extname(originalFile));
    const moduleDirName = path.basename(moduleDir);
    const entries = [
      ...analysis.functions.map(f => f.name),
      ...analysis.classes.map(c => c.name)
    ];

    // 读取原文件，提取 main 块
    const originalSource = fs.readFileSync(originalFile, 'utf-8');
    const mainBlock = this.extractPYMainBlock(originalSource);

    // 主入口文件放在模块目录内（不覆盖原文件！）
    const mainPath = path.join(moduleDir, `${baseName}_main.py`);
    
    const imports = entries.map(name => 
      `from ${moduleDirName}.${name} import ${name}`
    );
    
    let content = [
      '# Auto-generated entry file',
      `# Source: ${path.basename(originalFile)}`,
      '# Generated by auto-file-splitter',
      '',
      ...imports,
      ''
    ].join('\n');
    
    content += '\nif __name__ == "__main__":\n';
    
    if (mainBlock) {
      // 写入从原文件提取的执行代码，每行缩进4空格
      const mainLines = mainBlock.split('\n');
      for (const line of mainLines) {
        if (line.trim() === '' || line.trimStart().startsWith('#')) {
          content += `    ${line}\n`;
        } else {
          content += `    ${line}\n`;
        }
      }
    } else {
      content += '    # ⚠️ 未检测到原文件的执行代码\n';
      content += "    print('请从此入口文件调用拆分后的模块')\n";
    }
    
    fs.writeFileSync(mainPath, content, 'utf-8');
    console.log(`   ✅ 生成Python主入口: ${path.basename(mainPath)} (含原始执行逻辑)`);
  }

  /**
   * 转换为kebab-case
   */
  toKebabCase(str) {
    return str
      .replace(/([a-z])([A-Z])/g, '$1-$2')
      .replace(/([A-Z])([A-Z][a-z])/g, '$1-$2')
      .toLowerCase();
  }

  /**
   * 打印报告
   */
  printReport() {
    console.log('\n============================================================');
    console.log('📊 一键拆分报告');
    console.log('============================================================');
    console.log(`📁 扫描目录: ${this.targetDir}`);
    console.log(`📂 扫描文件: ${this.results.scanned} 个`);
    console.log(`⚠️  超限文件: ${this.results.oversized.length} 个`);
    console.log(`✅ 已拆分: ${this.results.split.length} 个`);
    console.log(`❌ 失败: ${this.results.errors.length} 个`);
    
    if (this.results.split.length > 0) {
      console.log('\n📦 拆分结果:');
      this.results.split.forEach(r => {
        console.log(`   • ${path.basename(r.file)} → ${path.basename(r.moduleDir)}/`);
      });
    }
    
    if (this.results.errors.length > 0) {
      console.log('\n❌ 失败详情:');
      this.results.errors.forEach(e => {
        console.log(`   • ${path.basename(e.file)}: ${e.error}`);
      });
    }
    
    console.log('\n============================================================');
    console.log('🎉 检查完成！');
    console.log('============================================================\n');
  }

  /**
   * Generate or update CODE_INDEX.md for the scanned directory
   */
  updateIndex() {
    const resolvedDir = path.resolve(this.targetDir);
    const indexScript = path.join(
      'c:\\Users\\ThinkPad\\.workbuddy\\skills',
      'python-file-splitter', 'scripts', 'generate_index.py'
    );

    if (!fs.existsSync(indexScript)) {
      console.log('⚠️  generate_index.py not found, skipping CODE_INDEX.md generation');
      return;
    }

    console.log('\n📑 Updating CODE_INDEX.md ...');
    try {
      const { execSync } = require('child_process');
      const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
      execSync(`${pythonCmd} "${indexScript}" "${resolvedDir}"`, {
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe']
      });
      console.log(`✅ CODE_INDEX.md updated: ${resolvedDir}\\CODE_INDEX.md`);
    } catch (e) {
      console.log(`⚠️  Could not update CODE_INDEX.md: ${e.message}`);
    }
  }
}

// CLI入口
function main() {
  const args = process.argv.slice(2);
  const targetDir = args[0] || '.';
  
  const splitter = new AutoFileSplitter(targetDir);
  splitter.run();
}

module.exports = { AutoFileSplitter };

if (require.main === module) {
  main();
}
