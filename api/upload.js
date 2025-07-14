import formidable from 'formidable';
import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { spawn } from 'child_process';
import { CSVToJSONConverter } from './csv_converter.js';

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
    return res.status(405).json({ error: 'Method not allowed' });
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
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const uploadedFile = files.file[0];
    const originalFilename = uploadedFile.originalFilename || 'unknown';
    
    // 验证文件类型 - 支持JSON和CSV
    const isJSON = originalFilename.toLowerCase().endsWith('.json');
    const isCSV = originalFilename.toLowerCase().endsWith('.csv');
    
    if (!isJSON && !isCSV) {
      return res.status(400).json({ error: 'Only JSON and CSV files are supported' });
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
      progress: 'Starting file processing...',
      filename: originalFilename,
      file_type: isCSV ? 'csv' : 'json',
      created_at: new Date().toISOString(),
      logs: ['File uploaded successfully', isCSV ? 'CSV file detected, will convert to JSON first' : 'JSON file detected, starting analysis...']
    };

    // 保存任务状态
    const statusPath = path.join(tmpDir, `task_${taskId}.json`);
    fs.writeFileSync(statusPath, JSON.stringify(taskStatus, null, 2));

    // 启动后台处理（异步）
    processFileWithConversion(filePath, taskId, tmpDir, resultsDir, isCSV).catch(error => {
      console.error('File processing error:', error);
      // 更新任务状态为错误
      const errorStatus = {
        ...taskStatus,
        status: 'error',
        progress: 'Processing failed',
        error: error.message,
        error_at: new Date().toISOString()
      };
      fs.writeFileSync(statusPath, JSON.stringify(errorStatus, null, 2));
    });
    
    return res.status(200).json({ task_id: taskId });

  } catch (error) {
    console.error('Upload error:', error);
    return res.status(500).json({ error: 'Upload failed: ' + error.message });
  }
}

async function processFileWithConversion(filePath, taskId, tmpDir, resultsDir, isCSV) {
  const statusPath = path.join(tmpDir, `task_${taskId}.json`);
  
  // 状态更新函数
  const updateStatus = (status, progress, logs = [], results = null) => {
    const currentStatus = JSON.parse(fs.readFileSync(statusPath, 'utf-8'));
    const updatedStatus = {
      ...currentStatus,
      status,
      progress,
      logs: [...currentStatus.logs, ...logs],
      ...(results && { results }),
      updated_at: new Date().toISOString()
    };
    fs.writeFileSync(statusPath, JSON.stringify(updatedStatus, null, 2));
  };

  try {
    let finalJsonPath = filePath;

    if (isCSV) {
      // CSV文件需要先转换为JSON
      updateStatus('processing', 'Converting CSV to JSON...', ['Starting CSV to JSON conversion...']);
      
      const converter = new CSVToJSONConverter();
      const jsonFilename = path.basename(filePath, '.csv') + '_converted.json';
      const jsonPath = path.join(path.dirname(filePath), jsonFilename);
      
      await converter.convertCSVToJSON(filePath, jsonPath, updateStatus);
      finalJsonPath = jsonPath;
      
      updateStatus('processing', 'CSV conversion completed, starting analysis...', ['✓ CSV successfully converted to JSON', 'Starting brand analysis...']);
    }

    // 使用JSON文件进行分析
    await processFileWithPython(finalJsonPath, taskId, tmpDir, resultsDir);
    
  } catch (error) {
    console.error('File conversion error:', error);
    updateStatus('error', 'File processing failed', [`Error: ${error.message}`]);
    throw error;
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

    updateStatus('processing', 'Starting Python analysis script...', ['Calling: python ' + pythonArgs.join(' ')]);

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
        updateStatus('processing', 'Analyzing...', lines);
      }
    });

    // 处理标准错误
    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString();
      stderr += error;
      console.error('Python stderr:', error);
      
      const errorLines = error.split('\n').filter(line => line.trim());
      logs.push(...errorLines.map(line => `ERROR: ${line}`));
      updateStatus('processing', 'Encountered issues during processing...', errorLines.map(line => `ERROR: ${line}`));
    });

    // 处理进程结束
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        // 成功完成，尝试读取结果文件
        try {
          const results = extractResultsFromOutput(stdout, resultsDir, filePath);
          updateStatus('completed', 'Analysis completed!', ['Python script executed successfully'], results);
          resolve(results);
        } catch (error) {
          console.error('Result extraction error:', error);
          updateStatus('error', 'Result processing failed', [`Result extraction error: ${error.message}`]);
          reject(error);
        }
      } else {
        const errorMsg = `Python script execution failed with exit code: ${code}`;
        updateStatus('error', errorMsg, [`Exit code: ${code}`, `stderr: ${stderr}`]);
        reject(new Error(errorMsg));
      }
    });

    // 处理进程错误
    pythonProcess.on('error', (error) => {
      console.error('Python process error:', error);
      updateStatus('error', 'Unable to start Python script', [`Process error: ${error.message}`]);
      reject(error);
    });
  });
}

function extractResultsFromOutput(stdout, resultsDir, inputFilePath) {
  // 从 Python 脚本输出中提取统计信息
  let baseFilename = path.basename(inputFilePath, '.json');
  
  // 如果是转换后的文件，移除 _converted 后缀
  if (baseFilename.endsWith('_converted')) {
    baseFilename = baseFilename.replace('_converted', '');
  }
  
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
    if (line.includes('总创作者数:') || line.includes('Total creators:')) {
      const match = line.match(/(\d+)/);
      if (match) totalProcessed = parseInt(match[1]);
    }
    if (line.includes('品牌相关账号:') || line.includes('Brand related accounts:')) {
      const match = line.match(/(\d+)/);
      if (match) brandRelatedCount = parseInt(match[1]);
    }
    if (line.includes('非品牌账号:') || line.includes('Non-brand accounts:')) {
      const match = line.match(/(\d+)/);
      if (match) nonBrandCount = parseInt(match[1]);
    }
    if ((line.includes('官方品牌账号:') || line.includes('Official brand accounts:')) && line.includes('brand_related_list')) {
      const match = line.match(/(\d+)/);
      if (match) brandCount = parseInt(match[1]);
    }
    if ((line.includes('矩阵账号:') || line.includes('Matrix accounts:')) && line.includes('brand_related_list')) {
      const match = line.match(/(\d+)/);
      if (match) matrixCount = parseInt(match[1]);
    }
    if ((line.includes('UGC创作者:') || line.includes('UGC creators:')) && line.includes('brand_related_list')) {
      const match = line.match(/(\d+)/);
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
    brand_count: brandCount,
    matrix_count: matrixCount,
    ugc_count: ugcCount,
    brand_percentage: brandPercentage,
    matrix_percentage: matrixPercentage,
    ugc_percentage: ugcPercentage,
    brand_file: brandFile,
    non_brand_file: nonBrandFile
  };
} 