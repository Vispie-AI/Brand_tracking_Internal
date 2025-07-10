import fs from 'fs';
import path from 'path';

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

  if (req.method !== 'GET') {
    return res.status(405).json({ error: '方法不允许' });
  }

  const { task_id, file_type } = req.query;

  if (!task_id || !file_type) {
    return res.status(400).json({ error: '缺少必要参数' });
  }

  try {
    const tmpDir = '/tmp/brand_analyzer';
    const statusPath = path.join(tmpDir, `task_${task_id}.json`);

    if (!fs.existsSync(statusPath)) {
      return res.status(404).json({ error: '任务不存在' });
    }

    const taskStatus = JSON.parse(fs.readFileSync(statusPath, 'utf-8'));
    
    if (taskStatus.status !== 'completed') {
      return res.status(400).json({ error: '任务尚未完成' });
    }

    let filename;
    if (file_type === 'brand_related') {
      filename = taskStatus.results.brand_file;
    } else if (file_type === 'non_brand') {
      filename = taskStatus.results.non_brand_file;
    } else {
      return res.status(400).json({ error: '无效的文件类型' });
    }

    const filePath = path.join(tmpDir, 'results', filename);
    
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: '文件不存在' });
    }

    const fileBuffer = fs.readFileSync(filePath);
    
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    
    return res.status(200).send(fileBuffer);

  } catch (error) {
    console.error('Download error:', error);
    return res.status(500).json({ error: '下载文件失败' });
  }
} 