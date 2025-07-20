from http.server import BaseHTTPRequestHandler
import json
import urllib.parse as urlparse

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
            
            # 模拟日志数据
            mock_logs = [
                'File uploaded successfully',
                'Starting creator data analysis...',
                'Loading 397 creators from uploaded file...',
                'Processing creator profiles (batch 1/13)...',
                'Analyzing brand associations with AI...',
                'Processing creator profiles (batch 3/13)...',
                'Found 35 official brand accounts...',
                'Processing creator profiles (batch 5/13)...',
                'Found 50 matrix accounts...',
                'Processing creator profiles (batch 8/13)...',
                'Found 216 UGC creators...',
                'Processing creator profiles (batch 10/13)...',
                'Found 51 non-branded creators...',
                'Processing creator profiles (batch 13/13)...',
                'Generating classification results...',
                'Creating downloadable reports...',
                'Analysis completed successfully!'
            ]
            
            response_data = {
                'task_id': task_id,
                'logs': mock_logs
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