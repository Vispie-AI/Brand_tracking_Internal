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
            
            # 模拟状态响应（实际应用中这里会查询数据库或缓存）
            # 为了演示，我们返回一个模拟的状态
            status_data = {
                'task_id': task_id,
                'status': 'completed',  # 可能的状态: pending, processing, completed, error
                'progress': '分析完成',
                'results': {
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
            }
            
            self._send_json_response(200, status_data)
            
        except Exception as e:
            self._send_error(500, f'Status check failed: {str(e)}')
    
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