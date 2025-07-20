import json
import os
import time
import threading
from datetime import datetime

# 任务状态存储目录
TASK_DIR = '/tmp/tasks'

def ensure_task_dir():
    """确保任务目录存在"""
    os.makedirs(TASK_DIR, exist_ok=True)

def get_task_file(task_id):
    """获取任务文件路径"""
    ensure_task_dir()
    return os.path.join(TASK_DIR, f"{task_id}.json")

def create_task(task_id, filename):
    """创建新任务"""
    task_data = {
        'task_id': task_id,
        'filename': filename,
        'status': 'processing',
        'progress': '开始分析...',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'logs': ['文件上传成功', '开始创作者数据分析...'],
        'results': None
    }
    
    task_file = get_task_file(task_id)
    with open(task_file, 'w') as f:
        json.dump(task_data, f, indent=2)
    
    # 启动分析任务
    threading.Thread(target=simulate_analysis, args=(task_id,), daemon=True).start()
    
    return task_data

def get_task(task_id):
    """获取任务状态"""
    task_file = get_task_file(task_id)
    if not os.path.exists(task_file):
        return None
    
    try:
        with open(task_file, 'r') as f:
            return json.load(f)
    except:
        return None

def update_task(task_id, updates):
    """更新任务状态"""
    task_data = get_task(task_id)
    if not task_data:
        return None
    
    task_data.update(updates)
    task_data['updated_at'] = datetime.now().isoformat()
    
    task_file = get_task_file(task_id)
    with open(task_file, 'w') as f:
        json.dump(task_data, f, indent=2)
    
    return task_data

def add_log(task_id, log_message):
    """添加日志消息"""
    task_data = get_task(task_id)
    if task_data:
        task_data['logs'].append(log_message)
        task_data['updated_at'] = datetime.now().isoformat()
        
        task_file = get_task_file(task_id)
        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)

def simulate_analysis(task_id):
    """模拟分析过程"""
    try:
        # 分析步骤
        analysis_steps = [
            ('loading', '加载创作者数据文件...', 2),
            ('processing_1', '处理创作者档案 (批次 1/13)...', 3),
            ('ai_analysis', '使用 Gemini AI 分析品牌关联...', 4),
            ('processing_3', '处理创作者档案 (批次 3/13)...', 3),
            ('finding_brands', '发现 35 个官方品牌账号...', 2),
            ('processing_5', '处理创作者档案 (批次 5/13)...', 3),
            ('finding_matrix', '发现 50 个矩阵账号...', 2),
            ('processing_8', '处理创作者档案 (批次 8/13)...', 3),
            ('finding_ugc', '发现 216 个 UGC 创作者...', 2),
            ('processing_10', '处理创作者档案 (批次 10/13)...', 3),
            ('finding_non_brand', '发现 51 个非品牌创作者...', 2),
            ('processing_13', '处理创作者档案 (批次 13/13)...', 3),
            ('generating', '生成分类结果...', 2),
            ('creating_reports', '创建可下载报告...', 2),
            ('completed', '分析完成！', 1)
        ]
        
        for i, (step, message, duration) in enumerate(analysis_steps):
            if step == 'completed':
                # 完成分析，设置结果
                results = {
                    'total_processed': 397,
                    'brand_related_count': 346,
                    'non_brand_count': 51,
                    'official_account_count': 35,
                    'matrix_account_count': 50,
                    'ugc_creator_count': 216,
                    'non_branded_creator_count': 51,
                    'official_account_percentage': 9,
                    'matrix_account_percentage': 13,
                    'ugc_creator_percentage': 54,
                    'non_branded_creator_percentage': 13,
                    'brand_in_related': 35,
                    'matrix_in_related': 50,
                    'ugc_in_related': 216,
                    'brand_in_related_percentage': 10,
                    'matrix_in_related_percentage': 14,
                    'ugc_in_related_percentage': 62,
                    'brand_file': 'brand_related_creators.csv',
                    'non_brand_file': 'non_brand_creators.csv'
                }
                
                update_task(task_id, {
                    'status': 'completed',
                    'progress': message,
                    'results': results
                })
            else:
                update_task(task_id, {
                    'status': 'processing',
                    'progress': message
                })
            
            add_log(task_id, message)
            time.sleep(duration)
            
    except Exception as e:
        update_task(task_id, {
            'status': 'error',
            'progress': f'分析失败: {str(e)}'
        })
        add_log(task_id, f'错误: {str(e)}')

def cleanup_old_tasks():
    """清理旧任务"""
    ensure_task_dir()
    current_time = time.time()
    
    for filename in os.listdir(TASK_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(TASK_DIR, filename)
            try:
                # 删除超过1小时的任务文件
                if current_time - os.path.getmtime(filepath) > 3600:
                    os.remove(filepath)
            except:
                pass 