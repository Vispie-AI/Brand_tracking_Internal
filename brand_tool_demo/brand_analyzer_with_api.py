#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌创作者分析器 - 使用TikTok API获取真实粉丝数据
"""

import json
import csv
import logging
import requests
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CreatorData:
    """创作者数据结构"""
    video_id: str
    author_link: str
    create_time: str  # 改为字符串格式的日期
    author_avatar: str
    thumbnail_url: str
    video_diggcount: int
    video_playcount: int
    author_followers: int
    author_followings: int
    author_unique_id: str
    author_nickname: str = ""
    video_sharecount: int = 0
    video_commentcount: int = 0
    signature: str = ""

class TiktokBrandAnalyzer:
    def __init__(self):
        self.api_key = "34ba1ae26fmsha15de959b0b5d6ep11e6e6jsn64ad77705138"
        self.api_host = "tiktok-scraper7.p.rapidapi.com"
        self.base_url = "https://tiktok-scraper7.p.rapidapi.com/user/info"
        
        # 品牌筛选条件
        self.brand_config = {
            "min_followers": 10000,
            "max_followers": 5000000,
            "min_engagement_rate": 2.0,
            "max_engagement_rate": 15.0,
            "min_video_plays": 5000,
            "brand_keywords": [
                "note", "study", "education", "learning", "school", "student",
                "knowledge", "skill", "course", "tutorial", "teach", "academic",
                "research", "university", "college", "homework", "exam", "test",
                "book", "read", "write", "journal", "diary", "planner", "organize",
                "productivity", "tips", "hack", "method", "strategy", "plan",
                "goal", "success", "motivation", "inspiration", "growth", "develop",
                "improvement", "progress", "achievement", "career", "professional",
                "business", "work", "job", "office", "meeting", "presentation",
                "schedule", "calendar", "deadline", "project", "task", "workflow"
            ]
        }

    def get_user_info(self, unique_id: str) -> Optional[Dict]:
        """获取用户信息"""
        if not unique_id or unique_id.strip() == "":
            logger.warning(f"Empty unique_id provided")
            return None
            
        headers = {
            'x-rapidapi-host': self.api_host,
            'x-rapidapi-key': self.api_key
        }
        
        params = {'unique_id': unique_id}
        
        try:
            logger.debug(f"正在获取用户信息: {unique_id}")
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 0 and 'data' in data:
                stats = data['data'].get('stats', {})
                user = data['data'].get('user', {})
                user_info = {
                    'followerCount': stats.get('followerCount', 0),
                    'followingCount': stats.get('followingCount', 0),
                    'heartCount': stats.get('heartCount', 0),
                    'videoCount': stats.get('videoCount', 0),
                    'signature': user.get('signature', ''),
                    'nickname': user.get('nickname', ''),
                    'avatarThumb': user.get('avatarThumb', '')
                }
                logger.info(f"成功获取用户 {unique_id}: 粉丝 {user_info['followerCount']:,}, 关注 {user_info['followingCount']:,}")
                return user_info
            else:
                if data.get('msg') == 'unique_id is invalid':
                    logger.warning(f"API返回错误，用户 {unique_id}: unique_id is invalid")
                    return "INVALID"
                else:
                    logger.warning(f"API返回错误，用户 {unique_id}: {data.get('msg', 'Unknown error')}")
                    return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败，用户 {unique_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"处理响应失败，用户 {unique_id}: {e}")
            return None

    def convert_timestamp_to_date(self, timestamp: int) -> str:
        """将时间戳转换为年月日格式"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d')
        except:
            return str(timestamp)

    def is_brand_account(self, signature: str, nickname: str, follower_count: int) -> bool:
        """判断是否为品牌账户"""
        signature_lower = signature.lower()
        nickname_lower = nickname.lower()
        
        # 品牌指标
        brand_indicators = [
            # 商业邮箱
            '@gmail.com', '@outlook.com', '@yahoo.com', '@hotmail.com',
            'email', 'contact', 'business', 'collab', 'work with me',
            'collaboration', 'inquiry', 'pr', 'partnership',
            
            # 商业关键词
            'shop', 'store', 'brand', 'company', 'business', 'official',
            'LLC', 'inc', 'corp', 'ltd', 'co.',
            
            # 链接和社媒
            'link', 'bio', 'website', 'ig:', 'instagram', 'youtube',
            'tiktok', 'twitter', 'facebook', 'linktree', 'linktr.ee',
            
            # 产品推广
            'affiliate', 'discount', 'code', 'promo', 'sale', 'offer',
            'free', 'download', 'get', 'use code', 'save',
            
            # 服务提供
            'service', 'coaching', 'consultant', 'expert', 'professional',
            'certified', 'trainer', 'instructor', 'teacher'
        ]
        
        brand_score = 0
        for indicator in brand_indicators:
            if indicator in signature_lower or indicator in nickname_lower:
                brand_score += 1
        
        # 粉丝数量也是品牌指标
        if follower_count > 50000:
            brand_score += 2
        elif follower_count > 20000:
            brand_score += 1
            
        return brand_score >= 2

    def calculate_engagement_rate(self, data: CreatorData) -> float:
        """计算互动率"""
        if data.video_playcount == 0:
            return 0.0
        
        total_interactions = data.video_diggcount + data.video_sharecount + data.video_commentcount
        engagement_rate = (total_interactions / data.video_playcount) * 100
        return round(engagement_rate, 2)

    def matches_brand_keywords(self, signature: str, nickname: str) -> bool:
        """检查是否匹配品牌关键词"""
        text = f"{signature} {nickname}".lower()
        return any(keyword in text for keyword in self.brand_config["brand_keywords"])

    def meets_criteria(self, data: CreatorData) -> tuple[bool, str]:
        """检查是否符合筛选条件"""
        reasons = []
        
        # 粉丝数量检查
        if data.author_followers < self.brand_config["min_followers"]:
            reasons.append(f"粉丝数不足({data.author_followers:,} < {self.brand_config['min_followers']:,})")
        
        if data.author_followers > self.brand_config["max_followers"]:
            reasons.append(f"粉丝数过多({data.author_followers:,} > {self.brand_config['max_followers']:,})")
        
        # 播放量检查
        if data.video_playcount < self.brand_config["min_video_plays"]:
            reasons.append(f"播放量不足({data.video_playcount:,} < {self.brand_config['min_video_plays']:,})")
        
        # 互动率检查
        engagement_rate = self.calculate_engagement_rate(data)
        if engagement_rate < self.brand_config["min_engagement_rate"]:
            reasons.append(f"互动率过低({engagement_rate}% < {self.brand_config['min_engagement_rate']}%)")
        
        if engagement_rate > self.brand_config["max_engagement_rate"]:
            reasons.append(f"互动率过高({engagement_rate}% > {self.brand_config['max_engagement_rate']}%)")
        
        # 品牌账户检查
        if not self.is_brand_account(data.signature, data.author_nickname, data.author_followers):
            reasons.append("非品牌账户")
        
        # 关键词匹配检查
        if not self.matches_brand_keywords(data.signature, data.author_nickname):
            reasons.append("不匹配品牌关键词")
        
        meets_all = len(reasons) == 0
        reason_text = "; ".join(reasons) if reasons else "符合所有条件"
        
        return meets_all, reason_text

    def process_creators(self, input_file: str) -> List[CreatorData]:
        """处理创作者数据"""
        logger.info(f"开始处理文件: {input_file}")
        
        # 读取原始数据
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        if not isinstance(data, list):
            raise ValueError("JSON文件应包含一个列表")
        
        logger.info(f"读取到 {len(data)} 个记录")
        
        # 每个视频记录保持独立，不合并
        creators_data = []
        unique_authors = set()
        
        for item in data:
            try:
                # 从嵌套结构中提取信息
                basic_info = item.get('basic_info', {})
                
                # 提取基本信息
                author_unique_id = basic_info.get('author_unique_id', '').strip()
                if not author_unique_id:
                    logger.warning(f"跳过空的 author_unique_id: {item.get('video_id', 'unknown')}")
                    continue
                
                # 转换时间戳为日期
                create_time_ts = int(basic_info.get('create_time', 0))
                create_time_str = self.convert_timestamp_to_date(create_time_ts)
                
                creator = CreatorData(
                    video_id=str(item.get('video_id', '')),
                    author_link=basic_info.get('author_link', ''),
                    create_time=create_time_str,
                    author_avatar=basic_info.get('author_avatar', ''),  # 可能没有这个字段，稍后从API获取
                    thumbnail_url=basic_info.get('thumbnail_url', ''),
                    video_diggcount=int(basic_info.get('video_diggcount', 0)),
                    video_playcount=int(basic_info.get('video_playcount', 0)),
                    author_followers=0,  # 先设为0，后面从API获取
                    author_followings=0,
                    author_unique_id=author_unique_id,
                    author_nickname=basic_info.get('author_nickname', ''),
                    video_sharecount=int(basic_info.get('video_sharecount', 0)),
                    video_commentcount=int(basic_info.get('video_commentcount', 0)),
                    signature=""  # 从API获取
                )
                
                creators_data.append(creator)
                unique_authors.add(author_unique_id)
                
            except Exception as e:
                logger.error(f"处理记录时出错: {e}, 记录: {item.get('video_id', 'unknown')}")
                continue
        
        logger.info(f"处理了 {len(creators_data)} 个视频记录，来自 {len(unique_authors)} 个唯一创作者")
        
        # 获取用户信息 - 按唯一作者批量获取
        logger.info("开始获取用户粉丝数据...")
        user_info_cache = {}
        
        # 分批处理，每批15个，避免API限制
        unique_authors_list = list(unique_authors)
        batch_size = 35
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            for i in range(0, len(unique_authors_list), batch_size):
                batch = unique_authors_list[i:i + batch_size]
                future_to_author = {
                    executor.submit(self.get_user_info, author): author 
                    for author in batch
                }
                
                for future in as_completed(future_to_author):
                    author = future_to_author[future]
                    try:
                        result = future.result()
                        if result == "INVALID":
                            logger.warning(f"删除无效用户: {author}")
                            user_info_cache[author] = "INVALID"
                        elif result:
                            user_info_cache[author] = result
                        else:
                            logger.warning(f"未能获取用户信息: {author}")
                    except Exception as e:
                        logger.error(f"获取用户信息时出错 {author}: {e}")
                
                # 批次间等待，避免API限制
                if i + batch_size < len(unique_authors_list):
                    logger.info(f"已处理 {min(i + batch_size, len(unique_authors_list))}/{len(unique_authors_list)} 个用户，等待3秒...")
                    time.sleep(3)
        
        # 过滤掉无效用户的数据，并更新用户信息
        valid_creators = []
        for creator in creators_data:
            if creator.author_unique_id in user_info_cache:
                user_info = user_info_cache[creator.author_unique_id]
                if user_info == "INVALID":
                    continue  # 跳过无效用户
                if isinstance(user_info, dict):
                    creator.author_followers = user_info.get('followerCount', 0)
                    creator.author_followings = user_info.get('followingCount', 0)
                    creator.signature = user_info.get('signature', '')
                    creator.author_nickname = user_info.get('nickname', creator.author_nickname)
                    if user_info.get('avatarThumb'):
                        creator.author_avatar = user_info['avatarThumb']
            
            valid_creators.append(creator)
        
        logger.info(f"有效创作者数据: {len(valid_creators)} 个视频记录")
        return valid_creators

    def save_to_csv(self, creators: List[CreatorData], output_file: str):
        """保存到CSV文件"""
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            
            # 写入表头
            headers = [
                'video_id', 'author_link', 'create_time', 'author_avatar', 'thumbnail_url',
                'video_diggcount', 'video_playcount', 'author_followers', 'author_followings',
                'author_unique_id', 'author_nickname', 'video_sharecount', 'video_commentcount', 'signature'
            ]
            writer.writerow(headers)
            
            # 写入数据
            for creator in creators:
                # 清理signature字段，移除换行符和其他可能导致问题的字符
                clean_signature = creator.signature.replace('\n', ' ').replace('\r', ' ').strip()
                
                writer.writerow([
                    creator.video_id,
                    creator.author_link,
                    creator.create_time,
                    creator.author_avatar,
                    creator.thumbnail_url,
                    creator.video_diggcount,
                    creator.video_playcount,
                    creator.author_followers,
                    creator.author_followings,
                    creator.author_unique_id,
                    creator.author_nickname,
                    creator.video_sharecount,
                    creator.video_commentcount,
                    clean_signature
                ])

    def analyze_and_filter(self, input_file: str = "creator_list.json", output_file: str = "brandlist.csv"):
        """主分析函数"""
        start_time = time.time()
        
        try:
            # 处理数据
            creators = self.process_creators(input_file)
            
            if not creators:
                logger.error("没有找到有效的创作者数据")
                return
            
            # 筛选符合条件的创作者
            logger.info("开始筛选符合品牌条件的创作者...")
            filtered_creators = []
            
            for creator in creators:
                meets_criteria, reason = self.meets_criteria(creator)
                if meets_criteria:
                    filtered_creators.append(creator)
                    logger.debug(f"✅ {creator.author_unique_id}: {reason}")
                else:
                    logger.debug(f"❌ {creator.author_unique_id}: {reason}")
            
            # 保存结果
            if filtered_creators:
                self.save_to_csv(filtered_creators, output_file)
                
                # 统计信息
                total_videos = len(creators)
                filtered_videos = len(filtered_creators)
                filter_rate = (filtered_videos / total_videos) * 100 if total_videos > 0 else 0
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                logger.info(f"""
=== 分析完成 ===
原始视频记录: {total_videos:,} 个
筛选后记录: {filtered_videos:,} 个
通过率: {filter_rate:.2f}%
处理时间: {processing_time/60:.1f} 分钟
输出文件: {output_file}
""")
                
                # 显示文件大小
                import os
                file_size = os.path.getsize(output_file)
                logger.info(f"输出文件大小: {file_size/1024:.1f} KB")
                
            else:
                logger.warning("没有找到符合条件的创作者")
                
        except Exception as e:
            logger.error(f"分析过程中出错: {e}")
            raise

def main():
    """主函数"""
    analyzer = TiktokBrandAnalyzer()
    analyzer.analyze_and_filter()

if __name__ == "__main__":
    main() 