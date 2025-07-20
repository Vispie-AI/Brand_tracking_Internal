"""
纯Python CSV处理器，不依赖pandas
"""

import csv
import os
from typing import List, Dict, Set

class CSVProcessor:
    """纯Python CSV处理器"""
    
    @staticmethod
    def read_csv(file_path: str) -> List[Dict]:
        """读取CSV文件并返回字典列表"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        rows = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                rows.append(row)
        
        return rows
    
    @staticmethod
    def get_unique_creators(data: List[Dict], unique_column: str = 'user_unique_id') -> List[Dict]:
        """根据指定列去重，返回唯一创作者"""
        seen_ids = set()
        unique_creators = []
        
        for row in data:
            creator_id = row.get(unique_column, '').strip()
            if creator_id and creator_id not in seen_ids:
                seen_ids.add(creator_id)
                unique_creators.append(row)
        
        return unique_creators
    
    @staticmethod
    def check_required_columns(data: List[Dict], required_columns: List[str]) -> List[str]:
        """检查必要列是否存在，返回缺失的列"""
        if not data:
            return required_columns
        
        available_columns = set(data[0].keys())
        missing_columns = [col for col in required_columns if col not in available_columns]
        
        return missing_columns
    
    @staticmethod
    def convert_row_to_creator_info(row: Dict) -> Dict:
        """将CSV行转换为创作者信息格式"""
        return {
            'user_unique_id': str(row.get('user_unique_id', '')).strip(),
            'video_id': str(row.get('video_id', '')).strip(),
            'signature': str(row.get('signature', '')).strip(),
            'author_followers_count': int(row.get('author_followers_count', 0)) if str(row.get('author_followers_count', '')).isdigit() else 0,
            'author_followings_count': int(row.get('author_followings_count', 0)) if str(row.get('author_followings_count', '')).isdigit() else 0,
            'videoCount': int(row.get('videoCount', 0)) if str(row.get('videoCount', '')).isdigit() else 0,
            'author_avatar': str(row.get('author_avatar', '')).strip(),
            'create_times': str(row.get('create_times', '')).strip(),
            'user_nickname': str(row.get('user_nickname', '')).strip(),
            'title': str(row.get('title', '')).strip(),
            'date': str(row.get('date', '')).strip()
        } 