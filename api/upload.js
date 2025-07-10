import formidable from 'formidable';
import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { spawn } from 'child_process';

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  // 设置 CORS 头
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: '方法不允许' });
  }

  try {
    // 创建临时目录
    const tmpDir = '/tmp/brand_analyzer';
    const uploadsDir = path.join(tmpDir, 'uploads');
    const resultsDir = path.join(tmpDir, 'analyzed_data');
    
    if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir, { recursive: true });
    if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir, { recursive: true });
    if (!fs.existsSync(resultsDir)) fs.mkdirSync(resultsDir, { recursive: true });

    // 解析上传的文件
    const form = formidable({
      uploadDir: uploadsDir,
      keepExtensions: true,
      maxFileSize: 50 * 1024 * 1024, // 50MB
    });

    const [fields, files] = await form.parse(req);
    
    if (!files.file || !files.file[0]) {
      return res.status(400).json({ error: '没有上传文件' });
    }

    const uploadedFile = files.file[0];
    const originalFilename = uploadedFile.originalFilename || 'unknown';
    
    // 验证文件类型 - 改为 JSON
    if (!originalFilename.toLowerCase().endsWith('.json')) {
      return res.status(400).json({ error: '只支持 JSON 文件' });
    }

    // 生成任务ID
    const taskId = uuidv4();
    const timestamp = new Date().toISOString().replace(/[:.-]/g, '');
    const processedFilename = `${timestamp}_${originalFilename}`;
    const filePath = path.join(uploadsDir, processedFilename);

    // 移动文件到最终位置
    fs.renameSync(uploadedFile.filepath, filePath);

    // 初始化任务状态
    const taskStatus = {
      task_id: taskId,
      status: 'processing',
      progress: '开始处理文件...',
      filename: originalFilename,
      created_at: new Date().toISOString(),
      logs: ['文件上传成功', '开始分析创作者数据...']
    };

    // 保存任务状态
    const statusPath = path.join(tmpDir, `task_${taskId}.json`);
    fs.writeFileSync(statusPath, JSON.stringify(taskStatus, null, 2));

    // 启动后台处理（异步）
    processFileWithPython(filePath, taskId, tmpDir, resultsDir).catch(error => {
      console.error('Python processing error:', error);
      // 更新任务状态为错误
      const errorStatus = {
        ...taskStatus,
        status: 'error',
        progress: '处理失败',
        error: error.message,
        error_at: new Date().toISOString()
      };
      fs.writeFileSync(statusPath, JSON.stringify(errorStatus, null, 2));
    });
    
    return res.status(200).json({ task_id: taskId });

  } catch (error) {
    console.error('Upload error:', error);
    return res.status(500).json({ error: '上传失败: ' + error.message });
  }
}

async function processFileWithPython(filePath, taskId, tmpDir, resultsDir) {
  return new Promise((resolve, reject) => {
    const statusPath = path.join(tmpDir, `task_${taskId}.json`);
    
    // 读取当前状态
    let currentStatus = JSON.parse(fs.readFileSync(statusPath, 'utf-8'));
    
    // 更新状态函数
    const updateStatus = (status, progress, logs = [], results = null) => {
      currentStatus = {
        ...currentStatus,
        status,
        progress,
        logs: [...currentStatus.logs, ...logs],
        ...(results && { results }),
        updated_at: new Date().toISOString()
      };
      fs.writeFileSync(statusPath, JSON.stringify(currentStatus, null, 2));
    };

    // 准备 Python 脚本路径和参数
    // 在 Vercel 中，项目文件可能在不同的路径
    let scriptPath = path.join(process.cwd(), 'universal_brand_analyzer.py');
    if (!fs.existsSync(scriptPath)) {
      // 尝试查找脚本的其他可能位置
      const alternativePaths = [
        path.join(process.cwd(), '..', 'universal_brand_analyzer.py'),
        path.join(__dirname, '..', 'universal_brand_analyzer.py'),
        path.join(__dirname, '..', '..', 'universal_brand_analyzer.py')
      ];
      
      for (const altPath of alternativePaths) {
        if (fs.existsSync(altPath)) {
          scriptPath = altPath;
          break;
        }
      }
    }
    const pythonArgs = [
      scriptPath,
      filePath,
      '--output-dir', resultsDir,
      '--batch-size', '35',
      '--max-workers', '7'
    ];

    updateStatus('processing', '启动 Python 分析脚本...', ['调用: python ' + pythonArgs.join(' ')]);

    // 启动 Python 进程
    const pythonProcess = spawn('python', pythonArgs, {
      cwd: process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';
    const logs = [];

    // 处理标准输出
    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      stdout += output;
      
      // 将输出按行分割并添加到日志
      const lines = output.split('\n').filter(line => line.trim());
      logs.push(...lines);
      
      // 更新状态和日志
      if (lines.length > 0) {
        updateStatus('processing', '正在分析...', lines);
      }
    });

    // 处理标准错误
    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString();
      stderr += error;
      console.error('Python stderr:', error);
      
      const errorLines = error.split('\n').filter(line => line.trim());
      logs.push(...errorLines.map(line => `ERROR: ${line}`));
      updateStatus('processing', '处理中遇到问题...', errorLines.map(line => `ERROR: ${line}`));
    });

    // 处理进程结束
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        // 成功完成，尝试读取结果文件
        try {
          const results = extractResultsFromOutput(stdout, resultsDir, filePath);
          updateStatus('completed', '分析完成！', ['Python 脚本执行成功'], results);
          resolve(results);
        } catch (error) {
          console.error('Result extraction error:', error);
          updateStatus('error', '结果处理失败', [`结果提取错误: ${error.message}`]);
          reject(error);
        }
      } else {
        const errorMsg = `Python 脚本执行失败，退出代码: ${code}`;
        updateStatus('error', errorMsg, [`退出代码: ${code}`, `stderr: ${stderr}`]);
        reject(new Error(errorMsg));
      }
    });

    // 处理进程错误
    pythonProcess.on('error', (error) => {
      console.error('Python process error:', error);
      updateStatus('error', '无法启动 Python 脚本', [`进程错误: ${error.message}`]);
      reject(error);
    });

    // 设置超时（5分钟）
    setTimeout(() => {
      if (!pythonProcess.killed) {
        pythonProcess.kill();
        updateStatus('error', '处理超时', ['任务执行超时，已终止进程']);
        reject(new Error('处理超时'));
      }
    }, 5 * 60 * 1000);
  });
}

function extractResultsFromOutput(stdout, resultsDir, inputFilePath) {
  // 从 Python 脚本输出中提取统计信息
  const baseFilename = path.basename(inputFilePath, '.json');
  
  // 查找生成的 CSV 文件
  const files = fs.readdirSync(resultsDir);
  const brandFile = files.find(f => f.includes(`${baseFilename}_brand_related_`) && f.endsWith('.csv'));
  const nonBrandFile = files.find(f => f.includes(`${baseFilename}_non_brand_`) && f.endsWith('.csv'));

  // 从标准输出中解析统计信息
  const lines = stdout.split('\n');
  
  let totalProcessed = 0;
  let brandRelatedCount = 0;
  let nonBrandCount = 0;
  let brandCount = 0;
  let matrixCount = 0;
  let ugcCount = 0;

  // 解析输出中的统计信息
  for (const line of lines) {
    if (line.includes('总创作者数:')) {
      const match = line.match(/总创作者数:\s*(\d+)/);
      if (match) totalProcessed = parseInt(match[1]);
    }
    if (line.includes('品牌相关账号:')) {
      const match = line.match(/品牌相关账号:\s*(\d+)/);
      if (match) brandRelatedCount = parseInt(match[1]);
    }
    if (line.includes('非品牌账号:')) {
      const match = line.match(/非品牌账号:\s*(\d+)/);
      if (match) nonBrandCount = parseInt(match[1]);
    }
    if (line.includes('官方品牌账号:') && line.includes('brand_related_list')) {
      const match = line.match(/官方品牌账号:\s*(\d+)/);
      if (match) brandCount = parseInt(match[1]);
    }
    if (line.includes('矩阵账号:') && line.includes('brand_related_list')) {
      const match = line.match(/矩阵账号:\s*(\d+)/);
      if (match) matrixCount = parseInt(match[1]);
    }
    if (line.includes('UGC创作者:') && line.includes('brand_related_list')) {
      const match = line.match(/UGC创作者:\s*(\d+)/);
      if (match) ugcCount = parseInt(match[1]);
    }
  }

  // 计算百分比
  const brandPercentage = brandRelatedCount > 0 ? Math.round((brandCount / brandRelatedCount) * 100) : 0;
  const matrixPercentage = brandRelatedCount > 0 ? Math.round((matrixCount / brandRelatedCount) * 100) : 0;
  const ugcPercentage = brandRelatedCount > 0 ? Math.round((ugcCount / brandRelatedCount) * 100) : 0;

  return {
    total_processed: totalProcessed,
    brand_related_count: brandRelatedCount,
    non_brand_count: nonBrandCount,
    brand_type_stats: {
      is_brand_count: brandCount,
      is_brand_percentage: brandPercentage,
      is_matrix_account_count: matrixCount,
      is_matrix_account_percentage: matrixPercentage,
      is_ugc_creator_count: ugcCount,
      is_ugc_creator_percentage: ugcPercentage
    },
    brand_file: brandFile,
    non_brand_file: nonBrandFile
  };
} 