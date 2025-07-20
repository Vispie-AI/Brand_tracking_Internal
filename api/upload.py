from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
from datetime import datetime
import cgi
import tempfile
import sys
import os
# 添加当前目录到Python路径，确保能导入task_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
try:
    from task_manager import create_task, cleanup_old_tasks
except ImportError:
    # 如果导入失败，定义简化版本
    def create_task(task_id, filename):
        return {'task_id': task_id, 'filename': filename}
    def cleanup_old_tasks():
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
                
                # 生成唯一的任务ID
                task_id = str(uuid.uuid4())
                
                # 处理文件保存（在 Vercel 中文件会被保存到临时目录）
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"{timestamp}_{filename}"
                
                # 读取文件内容
                file_content = file_item.file.read()
                
                # 清理旧任务
                cleanup_old_tasks()
                
                # 创建分析任务
                task_data = create_task(task_id, safe_filename)
                
                response_data = {
                    'message': 'File uploaded successfully',
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