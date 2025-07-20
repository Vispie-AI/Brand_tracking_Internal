import json
import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional

# 任务状态存储目录
TASK_DIR = '/tmp/tasks'

def ensure_task_dir():
    """确保任务目录存在"""
    os.makedirs(TASK_DIR, exist_ok=True)

def get_task_file(task_id):
    """获取任务文件路径"""
    ensure_task_dir()
    return os.path.join(TASK_DIR, f"{task_id}.json")

def get_logs_file(task_id):
    """获取日志文件路径"""
    ensure_task_dir()
    return os.path.join(TASK_DIR, f"{task_id}_logs.json")

def create_task(task_id: str, filename: str, total_creators: int = 0):
    """创建新任务"""
    task_data = {
        'task_id': task_id,
        'filename': filename,
        'status': 'pending',
        'progress': '准备开始分析...',
        'total_creators': total_creators,
        'completed_creators': 0,
        'failed_creators': 0,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'results': None
    }
    
    # 初始化日志
    logs_data = {
        'task_id': task_id,
        'logs': ['文件上传成功', '准备分析创作者数据...'],
        'updated_at': datetime.now().isoformat()
    }
    
    task_file = get_task_file(task_id)
    logs_file = get_logs_file(task_id)
    
    with open(task_file, 'w') as f:
        json.dump(task_data, f, indent=2)
    
    with open(logs_file, 'w') as f:
        json.dump(logs_data, f, indent=2)
    
    return task_data

def get_task(task_id: str) -> Optional[Dict]:
    """获取任务状态"""
    task_file = get_task_file(task_id)
    if not os.path.exists(task_file):
        return None
    
    try:
        with open(task_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading task file: {e}")
        return None

def update_task(task_id: str, updates: Dict):
    """更新任务状态"""
    task_data = get_task(task_id)
    if not task_data:
        return None
    
    task_data.update(updates)
    task_data['updated_at'] = datetime.now().isoformat()
    
    task_file = get_task_file(task_id)
    try:
        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)
        return task_data
    except Exception as e:
        print(f"Error updating task file: {e}")
        return None

def add_log(task_id: str, log_message: str):
    """添加日志消息"""
    logs_file = get_logs_file(task_id)
    
    try:
        # 读取现有日志
        if os.path.exists(logs_file):
            with open(logs_file, 'r') as f:
                logs_data = json.load(f)
        else:
            logs_data = {'task_id': task_id, 'logs': []}
        
        # 添加新日志
        logs_data['logs'].append(log_message)
        logs_data['updated_at'] = datetime.now().isoformat()
        
        # 保存日志
        with open(logs_file, 'w') as f:
            json.dump(logs_data, f, indent=2)
            
    except Exception as e:
        print(f"Error adding log: {e}")

def get_logs(task_id: str) -> List[str]:
    """获取任务日志"""
    logs_file = get_logs_file(task_id)
    
    if not os.path.exists(logs_file):
        return ['文件上传成功']
    
    try:
        with open(logs_file, 'r') as f:
            logs_data = json.load(f)
            return logs_data.get('logs', [])
    except Exception as e:
        print(f"Error reading logs file: {e}")
        return ['文件上传成功', f'读取日志时出错: {str(e)}']

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

def start_analysis_task(task_id: str, file_path: str):
    """启动分析任务（在后台线程中运行）"""
    def run_analysis():
        try:
            # 导入分析器
            import sys
            import os
            
            # 添加多个可能的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            
            sys.path.insert(0, current_dir)
            sys.path.insert(0, parent_dir)
            sys.path.insert(0, '/var/task')  # Vercel路径
            
            try:
                from universal_brand_analyzer import UniversalBrandAnalyzer
            except ImportError as e:
                print(f"Failed to import UniversalBrandAnalyzer: {e}")
                # 如果导入失败，创建一个简化的分析器
                class UniversalBrandAnalyzer:
                    def __init__(self, output_dir, custom_logger=None):
                        self.output_dir = output_dir
                        self.logger = custom_logger
                    
                    def analyze_creators_from_csv_direct(self, file_path):
                        # 返回模拟结果
                        return []
            
            # 更新状态为开始分析
            update_task(task_id, {
                'status': 'processing',
                'progress': '开始分析创作者数据...'
            })
            add_log(task_id, '开始分析创作者数据...')
            
            # 创建自定义日志处理器来实时更新任务状态
            class TaskLogger:
                def __init__(self, task_id):
                    self.task_id = task_id
                    
                def info(self, message):
                    print(f"[{task_id}] {message}")
                    add_log(self.task_id, message)
                    
                    # 解析特定的进度消息
                    if "分析进度:" in message:
                        update_task(self.task_id, {
                            'progress': message,
                            'status': 'processing'
                        })
                    elif "✅ 已完成并保存:" in message:
                        # 提取完成的创作者信息
                        parts = message.split('(')
                        if len(parts) > 1:
                            completed_info = parts[1].replace(' 个结果)', '').strip()
                            update_task(self.task_id, {
                                'progress': f'已完成分析: {completed_info}',
                                'status': 'processing'
                            })
                    
                def error(self, message):
                    print(f"[{task_id}] ERROR: {message}")
                    add_log(self.task_id, f'错误: {message}')
                    
                def warning(self, message):
                    print(f"[{task_id}] WARNING: {message}")
                    add_log(self.task_id, f'警告: {message}')
            
            # 初始化分析器
            analyzer = UniversalBrandAnalyzer(
                output_dir=f"/tmp/analysis_{task_id}",
                custom_logger=TaskLogger(task_id)
            )
            
            add_log(task_id, f'开始处理文件: {file_path}')
            
            # 执行分析
            results = analyzer.analyze_creators_from_csv_direct(file_path)
            
            # 计算统计数据
            if results:
                brand_related = [r for r in results if 
                               (r.extracted_brand_name and r.extracted_brand_name.strip()) or 
                               r.is_brand or r.is_matrix_account]
                non_brand = [r for r in results if r not in brand_related]
                
                official_brands = [r for r in brand_related if r.is_brand]
                matrix_accounts = [r for r in brand_related if r.is_matrix_account]
                ugc_in_brand = [r for r in brand_related if r.is_ugc_creator]
                
                analysis_results = {
                    'total_processed': len(results),
                    'brand_related_count': len(brand_related),
                    'non_brand_count': len(non_brand),
                    'official_account_count': len(official_brands),
                    'matrix_account_count': len(matrix_accounts),
                    'ugc_creator_count': len(ugc_in_brand),
                    'non_branded_creator_count': len(non_brand),
                    'official_account_percentage': round((len(official_brands)/len(results))*100, 1) if results else 0,
                    'matrix_account_percentage': round((len(matrix_accounts)/len(results))*100, 1) if results else 0,
                    'ugc_creator_percentage': round((len(ugc_in_brand)/len(results))*100, 1) if results else 0,
                    'non_branded_creator_percentage': round((len(non_brand)/len(results))*100, 1) if results else 0,
                    'brand_in_related': len(official_brands),
                    'matrix_in_related': len(matrix_accounts),
                    'ugc_in_related': len(ugc_in_brand),
                    'brand_in_related_percentage': round((len(official_brands)/len(brand_related))*100, 1) if brand_related else 0,
                    'matrix_in_related_percentage': round((len(matrix_accounts)/len(brand_related))*100, 1) if brand_related else 0,
                    'ugc_in_related_percentage': round((len(ugc_in_brand)/len(brand_related))*100, 1) if brand_related else 0,
                    'brand_file': 'brand_related_creators.csv',
                    'non_brand_file': 'non_brand_creators.csv'
                }
                
                # 更新为完成状态
                update_task(task_id, {
                    'status': 'completed',
                    'progress': '分析完成！',
                    'results': analysis_results,
                    'completed_creators': len(results)
                })
                add_log(task_id, f'分析完成！总共处理了 {len(results)} 个创作者')
                add_log(task_id, f'品牌相关账号: {len(brand_related)} 个')
                add_log(task_id, f'非品牌账号: {len(non_brand)} 个')
            else:
                update_task(task_id, {
                    'status': 'error',
                    'progress': '分析失败：没有找到有效的创作者数据'
                })
                add_log(task_id, '分析失败：没有找到有效的创作者数据')
                
        except Exception as e:
            error_msg = f'分析过程中发生错误: {str(e)}'
            update_task(task_id, {
                'status': 'error',
                'progress': error_msg
            })
            add_log(task_id, error_msg)
            print(f"Analysis error: {e}")
    
    # 在后台线程中启动分析
    threading.Thread(target=run_analysis, daemon=True).start() 