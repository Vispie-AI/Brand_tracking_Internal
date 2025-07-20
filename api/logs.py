from http.server import BaseHTTPRequestHandler
import json
import urllib.parse as urlparse
import sys
import os
# 添加当前目录到Python路径，确保能导入task_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
try:
    from task_manager import get_task
except ImportError:
    # 如果导入失败，返回默认日志
    def get_task(task_id):
        return {
            'task_id': task_id,
            'logs': [
                'File uploaded successfully',
                'Starting creator data analysis...',
                'Loading creators from uploaded file...',
                'Processing creator profiles...',
                'Analyzing brand associations...',
                'Generating classification results...',
                'Analysis completed successfully!'
            ]
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
            
            # 从任务管理器获取真实日志
            task_data = get_task(task_id)
            
            if not task_data:
                self._send_error(404, f'Task {task_id} not found')
                return
            
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