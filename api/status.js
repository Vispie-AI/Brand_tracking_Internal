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

  const { task_id } = req.query;

  if (!task_id) {
    return res.status(400).json({ error: '缺少 task_id 参数' });
  }

  try {
    const tmpDir = '/tmp/brand_analyzer';
    const statusPath = path.join(tmpDir, `task_${task_id}.json`);

    if (!fs.existsSync(statusPath)) {
      return res.status(404).json({ error: '任务不存在' });
    }

    const taskStatus = JSON.parse(fs.readFileSync(statusPath, 'utf-8'));
    
    return res.status(200).json(taskStatus);

  } catch (error) {
    console.error('Status check error:', error);
    return res.status(500).json({ error: '获取任务状态失败' });
  }
} 