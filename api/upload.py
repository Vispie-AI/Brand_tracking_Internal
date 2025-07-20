from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
import time
from datetime import datetime
import cgi
import tempfile
import sys
import os
# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
try:
    from memory_storage import create_task, cleanup_old_tasks, start_analysis_task
except ImportError as e:
    print(f"Could not import memory_storage: {e}")
    # Fallback 函数
    def create_task(task_id, filename, total_creators=0):
        return {'task_id': task_id, 'filename': filename, 'status': 'pending'}
    def cleanup_old_tasks():
        pass
    def start_analysis_task(task_id, file_path):
        pass

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/upload' or self.path == '/':
            try:
                # 解析表单数据
                content_type = self.headers['content-type']
                if not content_type:
                    self._send_error(400, 'Content-Type header required')
                    return
                
                # 创建临时文件来处理上传
                form_data = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                if 'file' not in form_data:
                    self._send_error(400, 'No file selected')
                    return
                
                file_item = form_data['file']
                if not file_item.filename:
                    self._send_error(400, 'No file selected')
                    return
                
                # 检查文件类型
                filename = file_item.filename
                if not self._allowed_file(filename):
                    self._send_error(400, 'File type not allowed. Please upload CSV or JSON files.')
                    return
                
                # 生成包含时间戳的任务ID，用于基于时间计算分析进度
                timestamp_part = str(int(time.time()))
                uuid_part = str(uuid.uuid4())[:8]
                task_id = f"{timestamp_part}-{uuid_part}"
                
                # 处理文件保存（在 Vercel 中文件会被保存到临时目录）
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"{timestamp}_{filename}"
                
                # 读取文件内容
                file_content = file_item.file.read()
                
                # 保存文件到临时目录
                file_path = os.path.join(tempfile.gettempdir(), safe_filename)
                with open(file_path, 'wb') as temp_file:
                    temp_file.write(file_content)
                
                # 清理旧任务
                cleanup_old_tasks()
                
                # 创建分析任务
                task_data = create_task(task_id, safe_filename)
                
                # 启动真实的分析任务
                start_analysis_task(task_id, file_path)
                
                response_data = {
                    'message': 'File uploaded successfully and analysis started',
                    'task_id': task_id,
                    'filename': safe_filename,
                    'size': len(file_content)
                }
                
                self._send_json_response(200, response_data)
                
            except Exception as e:
                self._send_error(500, f'Upload failed: {str(e)}')
        else:
            self._send_error(404, 'Not found')
    
    def do_OPTIONS(self):
        # 处理 CORS preflight 请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _allowed_file(self, filename):
        ALLOWED_EXTENSIONS = {'csv', 'json'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
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