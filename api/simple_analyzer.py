"""
简化的品牌分析器，专门用于Vercel Serverless环境
"""

import json
import os
import time
import random
from datetime import datetime
from typing import List, Dict

class SimpleBrandAnalyzer:
    """简化的品牌分析器"""
    
    def __init__(self, output_dir: str = "/tmp", custom_logger=None):
        self.output_dir = output_dir
        self.logger = custom_logger or self._default_logger()
        os.makedirs(output_dir, exist_ok=True)
    
    def _default_logger(self):
        """默认日志处理器"""
        class DefaultLogger:
            def info(self, message):
                print(f"[INFO] {message}")
            def error(self, message):
                print(f"[ERROR] {message}")
            def warning(self, message):
                print(f"[WARNING] {message}")
        return DefaultLogger()
    
    def analyze_creators_from_csv_direct(self, file_path: str) -> List[Dict]:
        """分析CSV文件中的创作者"""
        try:
            import pandas as pd
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            self.logger.info(f"CSV文件包含 {len(df)} 行数据")
            
            # 检查必要的列
            required_columns = ['user_unique_id', 'video_id']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.error(f"CSV文件缺少必要列: {missing_columns}")
                return []
            
            # 提取唯一的创作者
            unique_creators = df.drop_duplicates(subset=['user_unique_id'])
            self.logger.info(f"发现 {len(unique_creators)} 个唯一创作者")
            
            results = []
            
            # 模拟分析过程
            for idx, (_, row) in enumerate(unique_creators.iterrows()):
                user_id = str(row['user_unique_id']).strip()
                signature = str(row.get('signature', '')).strip()
                
                # 模拟分析延迟
                time.sleep(0.1)
                
                # 基于签名进行简单的品牌检测
                is_brand = self._detect_brand_from_signature(signature)
                extracted_brand = self._extract_brand_name(signature) if is_brand else ""
                
                # 确定账号类型
                account_type = self._determine_account_type(signature, user_id)
                
                result = {
                    'video_id': str(row.get('video_id', '')),
                    'author_unique_id': user_id,
                    'author_link': f"https://tiktok.com/@{user_id}",
                    'signature': signature,
                    'is_brand': is_brand,
                    'is_matrix_account': account_type == 'matrix',
                    'is_ugc_creator': account_type == 'ugc',
                    'extracted_brand_name': extracted_brand,
                    'brand_confidence': 0.8 if is_brand else 0.1,
                    'analysis_details': f"基于签名分析: {signature}",
                    'author_followers_count': int(row.get('author_followers_count', 0)),
                    'author_followings_count': int(row.get('author_followings_count', 0)),
                    'videoCount': int(row.get('videoCount', 0)),
                    'author_avatar': str(row.get('author_avatar', '')),
                    'create_times': str(row.get('create_times', '')),
                    'email': '',
                    'recent_20_posts_views_avg': 0.0,
                    'recent_20_posts_like_avg': 0.0,
                    'recent_20_posts_share_avg': 0.0,
                    'posting_frequency': 0.0,
                    'stability_score': 0.0,
                    'brands_in_videos': []
                }
                
                results.append(result)
                
                # 更新进度
                progress = (idx + 1) / len(unique_creators) * 100
                self.logger.info(f"分析进度: {idx + 1}/{len(unique_creators)} ({progress:.1f}%)")
            
            self.logger.info(f"分析完成，处理了 {len(results)} 个创作者")
            return results
            
        except Exception as e:
            self.logger.error(f"分析过程中发生错误: {str(e)}")
            return []
    
    def _detect_brand_from_signature(self, signature: str) -> bool:
        """从签名中检测品牌关联"""
        signature_lower = signature.lower()
        
        # 品牌关键词
        brand_keywords = [
            'official', 'brand', 'company', 'enterprise', 'corp', 'inc', 'ltd',
            'nike', 'adidas', 'apple', 'samsung', 'microsoft', 'google',
            'amazon', 'facebook', 'instagram', 'tiktok', 'youtube'
        ]
        
        return any(keyword in signature_lower for keyword in brand_keywords)
    
    def _extract_brand_name(self, signature: str) -> str:
        """从签名中提取品牌名称"""
        signature_lower = signature.lower()
        
        # 常见品牌名称
        brands = {
            'nike': 'Nike',
            'adidas': 'Adidas', 
            'apple': 'Apple',
            'samsung': 'Samsung',
            'microsoft': 'Microsoft',
            'google': 'Google',
            'amazon': 'Amazon',
            'facebook': 'Facebook',
            'instagram': 'Instagram',
            'tiktok': 'TikTok',
            'youtube': 'YouTube'
        }
        
        for brand_key, brand_name in brands.items():
            if brand_key in signature_lower:
                return brand_name
        
        return ""
    
    def _determine_account_type(self, signature: str, user_id: str) -> str:
        """确定账号类型"""
        signature_lower = signature.lower()
        user_id_lower = user_id.lower()
        
        # 官方账号特征
        if any(keyword in signature_lower for keyword in ['official', 'brand', 'company']):
            return 'official'
        
        # 矩阵账号特征
        if any(keyword in signature_lower for keyword in ['matrix', 'agency', 'management']):
            return 'matrix'
        
        # UGC创作者特征
        if any(keyword in signature_lower for keyword in ['creator', 'influencer', 'content']):
            return 'ugc'
        
        # 默认为非品牌
        return 'non_brand' 