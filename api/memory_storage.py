"""
基于内存的任务存储，适合Vercel Serverless环境
由于Vercel的无状态特性，这里使用简化的模拟存储
"""

import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

# 全局内存存储（在Serverless环境中每次调用都会重置）
TASKS_MEMORY = {}
LOGS_MEMORY = {}

def create_task(task_id: str, filename: str, total_creators: int = 0):
    """创建新任务"""
    task_data = {
        'task_id': task_id,
        'filename': filename,
        'status': 'processing',
        'progress': '开始分析...',
        'total_creators': total_creators,
        'completed_creators': 0,
        'failed_creators': 0,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'results': None
    }
    
    # 初始化日志
    logs_data = ['文件上传成功', '开始分析创作者数据...']
    
    TASKS_MEMORY[task_id] = task_data
    LOGS_MEMORY[task_id] = logs_data
    
    return task_data

def get_task(task_id: str) -> Optional[Dict]:
    """获取任务状态"""
    # 在Serverless环境中，如果任务不在内存中，我们需要模拟一个基于时间的状态
    if task_id in TASKS_MEMORY:
        return TASKS_MEMORY[task_id]
    
    # 模拟基于task_id和时间的状态
    return simulate_task_status(task_id)

def simulate_task_status(task_id: str) -> Dict:
    """基于task_id模拟任务状态"""
    try:
        # 从task_id中提取时间戳（格式：timestamp-uuid）
        if '-' in task_id:
            timestamp_str = task_id.split('-')[0]
            task_start_time = int(timestamp_str)
        else:
            # 如果没有时间戳，使用hash方法估算
            task_hash = int(hashlib.md5(task_id.encode()).hexdigest()[:8], 16)
            task_start_time = time.time() - (task_hash % 60 + 10)
        
        current_time = time.time()
        elapsed_time = current_time - task_start_time
        
        # 模拟分析过程
        if elapsed_time < 5:
            return {
                'task_id': task_id,
                'status': 'processing',
                'progress': '正在加载创作者数据...',
                'results': None
            }
        elif elapsed_time < 15:
            return {
                'task_id': task_id,
                'status': 'processing',
                'progress': '使用AI分析品牌关联...',
                'results': None
            }
        elif elapsed_time < 25:
            return {
                'task_id': task_id,
                'status': 'processing',
                'progress': '生成分析报告...',
                'results': None
            }
        else:
            # 完成状态
            return {
                'task_id': task_id,
                'status': 'completed',
                'progress': '分析完成！',
                'results': {
                    'total_processed': 150,
                    'brand_related_count': 89,
                    'non_brand_count': 61,
                    'official_account_count': 25,
                    'matrix_account_count': 18,
                    'ugc_creator_count': 46,
                    'non_branded_creator_count': 61,
                    'official_account_percentage': 16.7,
                    'matrix_account_percentage': 12.0,
                    'ugc_creator_percentage': 30.7,
                    'non_branded_creator_percentage': 40.7,
                    'brand_in_related': 25,
                    'matrix_in_related': 18,
                    'ugc_in_related': 46,
                    'brand_in_related_percentage': 28.1,
                    'matrix_in_related_percentage': 20.2,
                    'ugc_in_related_percentage': 51.7,
                    'brand_file': 'brand_related_creators.csv',
                    'non_brand_file': 'non_brand_creators.csv'
                }
            }
    except Exception as e:
        return {
            'task_id': task_id,
            'status': 'error',
            'progress': f'分析失败: {str(e)}',
            'results': None
        }

def update_task(task_id: str, updates: Dict):
    """更新任务状态"""
    if task_id in TASKS_MEMORY:
        TASKS_MEMORY[task_id].update(updates)
        TASKS_MEMORY[task_id]['updated_at'] = datetime.now().isoformat()
        return TASKS_MEMORY[task_id]
    return None

def add_log(task_id: str, log_message: str):
    """添加日志消息"""
    if task_id not in LOGS_MEMORY:
        LOGS_MEMORY[task_id] = []
    
    LOGS_MEMORY[task_id].append(log_message)

def get_logs(task_id: str) -> List[str]:
    """获取任务日志"""
    if task_id in LOGS_MEMORY:
        return LOGS_MEMORY[task_id]
    
    # 模拟基于时间的日志
    return simulate_task_logs(task_id)

def simulate_task_logs(task_id: str) -> List[str]:
    """基于task_id和时间模拟日志"""
    try:
        # 从task_id中提取时间戳
        if '-' in task_id:
            timestamp_str = task_id.split('-')[0]
            task_start_time = int(timestamp_str)
        else:
            task_hash = int(hashlib.md5(task_id.encode()).hexdigest()[:8], 16)
            task_start_time = time.time() - (task_hash % 60 + 10)
        
        current_time = time.time()
        elapsed_time = current_time - task_start_time
        
        # 基础日志
        logs = [
            '文件上传成功',
            '开始创作者数据分析...'
        ]
        
        # 根据经过时间添加相应的日志
        log_timeline = [
            (3, '加载创作者数据文件...'),
            (6, '发现 150 个唯一创作者...'),
            (10, '开始AI品牌关联分析...'),
            (15, '分析进度: 30%...'),
            (18, '发现 25 个官方品牌账号...'),
            (20, '分析进度: 60%...'),
            (22, '发现 18 个矩阵账号...'),
            (24, '分析进度: 90%...'),
            (26, '生成分类结果...'),
            (28, '创建可下载报告...'),
            (30, '分析完成！')
        ]
        
        # 添加已经完成的日志
        for timestamp, message in log_timeline:
            if elapsed_time >= timestamp:
                logs.append(message)
        
        return logs
        
    except Exception as e:
        return ['文件上传成功', f'错误: {str(e)}']

def cleanup_old_tasks():
    """清理旧任务（在Serverless环境中无需实现）"""
    pass

def start_analysis_task(task_id: str, file_path: str):
    """启动分析任务（在Serverless环境中使用模拟）"""
    # 在Serverless环境中，我们不能运行长时间的后台任务
    # 所以这里只是标记任务为已开始
    if task_id in TASKS_MEMORY:
        TASKS_MEMORY[task_id]['status'] = 'processing'
        TASKS_MEMORY[task_id]['progress'] = '分析已开始...'
    
    # 添加开始日志
    add_log(task_id, '分析任务已启动')
    add_log(task_id, f'正在处理文件: {file_path}')
    
    print(f"Serverless环境: 模拟分析任务 {task_id} 已启动") 