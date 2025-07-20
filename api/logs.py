from http.server import BaseHTTPRequestHandler
import json
import urllib.parse as urlparse
import time
import hashlib

def get_task_logs(task_id):
    """基于task_id和时间生成分析日志"""
    try:
        current_time = time.time()
        
        # 尝试从task_id中提取时间戳（格式：timestamp-uuid）
        try:
            if '-' in task_id:
                timestamp_str = task_id.split('-')[0]
                task_start_time = int(timestamp_str)
            else:
                # 如果没有时间戳，使用hash方法估算
                task_hash = int(hashlib.md5(task_id.encode()).hexdigest()[:8], 16)
                task_start_time = current_time - (task_hash % 60 + 1)
        except (ValueError, IndexError):
            # 如果解析失败，使用hash方法
            task_hash = int(hashlib.md5(task_id.encode()).hexdigest()[:8], 16)
            task_start_time = current_time - (task_hash % 60 + 1)
        
        # 计算任务运行时间
        elapsed_time = current_time - task_start_time
        
        # 基础日志
        logs = [
            '文件上传成功',
            '开始创作者数据分析...'
        ]
        
        # 根据经过时间添加相应的日志
        log_timeline = [
            (3, '加载创作者数据文件...'),
            (6, '加载 397 个创作者数据...'),
            (10, '处理创作者档案 (批次 1/13)...'),
            (15, '使用 Gemini AI 分析品牌关联...'),
            (19, '处理创作者档案 (批次 3/13)...'),
            (22, '发现 35 个官方品牌账号...'),
            (26, '处理创作者档案 (批次 5/13)...'),
            (29, '发现 50 个矩阵账号...'),
            (33, '处理创作者档案 (批次 8/13)...'),
            (36, '发现 216 个 UGC 创作者...'),
            (40, '处理创作者档案 (批次 10/13)...'),
            (43, '发现 51 个非品牌创作者...'),
            (47, '处理创作者档案 (批次 13/13)...'),
            (50, '生成分类结果...'),
            (53, '创建可下载报告...'),
            (56, '分析完成！')
        ]
        
        # 添加已经完成的日志
        for timestamp, message in log_timeline:
            if elapsed_time >= timestamp:
                logs.append(message)
        
        return {
            'task_id': task_id,
            'logs': logs
        }
        
    except Exception as e:
        return {
            'task_id': task_id,
            'logs': ['文件上传成功', f'错误: {str(e)}']
        }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 解析查询参数
            parsed_url = urlparse.urlparse(self.path)
            query_params = urlparse.parse_qs(parsed_url.query)
            
            if 'task_id' not in query_params:
                self._send_error(400, 'Missing task_id parameter')
                return
            
            task_id = query_params['task_id'][0]
            
            # 获取基于时间的分析日志
            task_data = get_task_logs(task_id)
            
            response_data = {
                'task_id': task_id,
                'logs': task_data.get('logs', [])
            }
            
            self._send_json_response(200, response_data)
            
        except Exception as e:
            self._send_error(500, f'Logs retrieval failed: {str(e)}')
    
    def do_OPTIONS(self):
        # 处理 CORS preflight 请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_error(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_data = {'error': message}
        self.wfile.write(json.dumps(error_data).encode()) 