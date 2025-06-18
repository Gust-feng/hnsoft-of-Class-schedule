#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整个学期课表爬虫脚本
专门用于获取整个学期所有周的课程表数据
"""

import requests
import json
import time
import os
import subprocess
import sys
import glob
from datetime import datetime
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class AllWeeksScheduleCrawler:
    """
    整个学期课表爬虫类
    """
    
    def __init__(self):
        self.base_url = "http://222.243.161.213:81"
        self.session = requests.Session()
        self.token = None
        self.user_info = None
        
        # 通用请求头
        self.headers = {
            'Host': '222.243.161.213:81',
            'Cache-Control': 'no-cache',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Origin': 'http://222.243.161.213:81',
            'Referer': 'http://222.243.161.213:81/hnrjzyxysjd/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
    
    def login(self, user_no, password):
        """
        登录系统
        
        Args:
            user_no (str): 学号
            password (str): 密码（Base64编码后的）
            
        Returns:
            bool: 登录是否成功
        """
        print(f"正在登录用户: {user_no}")
        
        # 登录URL和参数
        login_url = f"{self.base_url}/hnrjzyxyhd/login"
        login_params = {
            'userNo': user_no,
            'pwd': password,
            'encode': '1',
            'captchaData': '',
            'codeVal': ''
        }
        
        # 设置登录请求头
        login_headers = self.headers.copy()
        login_headers['token'] = 'null'
        login_headers['Content-Length'] = '0'
        
        try:
            # 发送登录请求
            response = self.session.post(
                login_url, 
                params=login_params, 
                headers=login_headers, 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == '1':  # 登录成功
                    self.token = data['data']['token']
                    self.user_info = data['data']
                    
                    print(f"登录成功！欢迎 {self.user_info['name']}")
                    print(f"学院: {self.user_info['academyName']}")
                    print(f"班级: {self.user_info['clsName']}")
                    print(f"Token: {self.token[:50]}...")
                    
                    # 保存登录响应
                    self._save_response(response.text, "all_weeks_login")
                    return True
                else:
                    print(f"登录失败: {data.get('Msg', '未知错误')}")
                    return False
            else:
                print(f"登录请求失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"登录过程发生错误: {e}")
            return False
    
    def get_teaching_week(self):
        """
        获取教学周信息
        """
        if not self.token:
            print("错误: 请先登录")
            return None
            
        try:
            url = f"{self.base_url}/hnrjzyxyhd/teachingWeek"
            headers = self.headers.copy()
            headers['token'] = self.token
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            # 保存响应到文件
            self._save_response(response.text, "all_weeks_teaching_week")
            
            try:
                data = response.json()
                print("教学周信息获取成功")
                return data
            except json.JSONDecodeError:
                print("教学周响应不是有效的JSON格式")
                return None
                
        except Exception as e:
            print(f"获取教学周信息时出错: {e}")
            return None
    
    def get_course_schedule_data(self, week="", kbjcmsid=""):
        """
        获取指定周的课程表数据
        
        Args:
            week (str): 周次
            kbjcmsid (str): 课表模式ID
            
        Returns:
            dict: 课程表数据
        """
        if not self.token:
            print("错误: 请先登录")
            return None
            
        try:
            # 使用真实的课程表数据接口
            url = f"{self.base_url}/hnrjzyxyhd/student/curriculum"
            params = {
                'week': week,
                'kbjcmsid': kbjcmsid
            }
            
            headers = self.headers.copy()
            headers['token'] = self.token
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            # 保存响应到文件
            week_suffix = f"_week{week}" if week else ""
            self._save_response(response.text, f"all_weeks_schedule_data{week_suffix}")
            
            # 尝试解析JSON响应
            try:
                data = response.json()
                if data.get('code') == '1' or data.get('code') == 1 or 'data' in data:
                    print(f"课程表数据获取成功 (第{week}周)" if week else "课程表数据获取成功")
                    return data
                else:
                    print(f"课程表数据获取失败: {data.get('Msg', data.get('msg', '未知错误'))}")
                    return None
            except json.JSONDecodeError:
                print("响应不是有效的JSON格式")
                return None
                
        except Exception as e:
            print(f"获取课程表数据时出错: {e}")
            return None
    
    def get_all_weeks_schedule(self, max_week=22, kbjcmsid=""):
        """
        获取所有周的课程表数据
        
        Args:
            max_week (int): 最大周数
            kbjcmsid (str): 课表模式ID
            
        Returns:
            dict: 包含所有周课程表数据的字典
        """
        if not self.token:
            print("错误: 请先登录")
            return None
            
        print(f"开始获取第1-{max_week}周的课程表数据...")
        all_weeks_data = {}
        success_count = 0
        failed_weeks = []
        
        for week in range(1, max_week + 1):
            print(f"正在获取第{week}周课程表数据...")
            
            week_data = self.get_course_schedule_data(str(week), kbjcmsid)
            if week_data:
                all_weeks_data[f"week_{week}"] = week_data
                success_count += 1
                print(f"第{week}周数据获取成功")
            else:
                failed_weeks.append(week)
                print(f"第{week}周数据获取失败")
            
            # 避免请求过快，每次请求后等待
            time.sleep(0.5)
        
        print(f"\n所有周数据获取完成")
        print(f"成功获取: {success_count} 周")
        if failed_weeks:
            print(f"失败周数: {failed_weeks}")
        
        return all_weeks_data
    
    def get_time_schedule_mode(self):
        """
        获取时间课表模式
        """
        if not self.token:
            print("错误: 请先登录")
            return None
            
        try:
            url = f"{self.base_url}/hnrjzyxyhd/Get_sjkbms"
            headers = self.headers.copy()
            headers['token'] = self.token
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            # 保存响应到文件
            self._save_response(response.text, "all_weeks_time_schedule_mode")
            
            try:
                data = response.json()
                print("时间课表模式获取成功")
                return data
            except json.JSONDecodeError:
                print("时间课表模式响应不是有效的JSON格式")
                return None
                
        except Exception as e:
            print(f"获取时间课表模式时出错: {e}")
            return None
    
    def _save_response(self, content, response_type):
        """
        保存响应内容到文件
        
        Args:
            content (str): 响应内容
            response_type (str): 响应类型
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{response_type}_response_{timestamp}.html"
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"{response_type}响应已保存到: {filepath}")
        except Exception as e:
            print(f"保存{response_type}响应失败: {e}")
    
    def crawl_all_weeks(self, user_no, password, max_week=22):
        """
        执行整个学期课表爬取流程
        
        Args:
            user_no (str): 学号
            password (str): 密码（Base64编码后的）
            max_week (int): 最大周数
            
        Returns:
            dict: 包含所有周爬取数据的字典
        """
        print("开始执行整个学期课表爬取流程")
        print("=" * 60)
        
        results = {
            'login_success': False,
            'user_info': None,
            'teaching_week': None,
            'time_schedule_mode': None,
            'all_weeks_data': None,
            'max_week': max_week,
            'success_weeks': [],
            'failed_weeks': []
        }
        
        # 步骤1: 登录
        if self.login(user_no, password):
            results['login_success'] = True
            results['user_info'] = self.user_info
            
            # 等待一秒，避免请求过快
            time.sleep(1)
            
            # 步骤2: 获取教学周信息
            teaching_week = self.get_teaching_week()
            if teaching_week:
                results['teaching_week'] = teaching_week
                
                # 从教学周信息中获取最大周数
                try:
                    if teaching_week.get('data') and len(teaching_week['data']) > 0:
                        max_week_from_api = max([int(week.get('zc', 0)) for week in teaching_week['data']])
                        if max_week_from_api > 0:
                            max_week = max_week_from_api
                            results['max_week'] = max_week
                            print(f"从API获取到最大周数: {max_week}")
                except Exception as e:
                    print(f"解析最大周数失败，使用默认值: {e}")
            
            # 等待一秒
            time.sleep(1)
            
            # 步骤3: 获取时间课表模式
            time_schedule_mode = self.get_time_schedule_mode()
            if time_schedule_mode:
                results['time_schedule_mode'] = time_schedule_mode
            
            # 等待一秒
            time.sleep(1)
            
            # 步骤4: 获取所有周的课程表数据
            print(f"\n开始获取所有周的课程表数据 (1-{max_week}周)...")
            all_weeks_data = self.get_all_weeks_schedule(max_week)
            if all_weeks_data:
                results['all_weeks_data'] = all_weeks_data
                
                # 统计成功和失败的周数
                for week in range(1, max_week + 1):
                    if f"week_{week}" in all_weeks_data:
                        results['success_weeks'].append(week)
                    else:
                        results['failed_weeks'].append(week)
        
        print("\n" + "=" * 60)
        print("整个学期爬取流程完成")
        
        return results
    
    def save_raw_data(self, data, filename_prefix="all_weeks_raw_data"):
        """
        保存原始数据到JSON文件
        
        Args:
            data (dict): 原始数据
            filename_prefix (str): 文件名前缀
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"原始数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            print(f"保存原始数据失败: {e}")
            return None
    
    def save_individual_week_data(self, all_weeks_data):
        """
        保存每周的单独数据文件
        
        Args:
            all_weeks_data (dict): 所有周的数据
        """
        if not all_weeks_data:
            return
        
        print("\n保存各周单独数据文件...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for week_key, week_data in all_weeks_data.items():
            week_number = week_key.replace('week_', '')
            filename = f"week_{week_number}_raw_data_{timestamp}.json"
            filepath = os.path.join(os.getcwd(), filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(week_data, f, ensure_ascii=False, indent=2)
                print(f"第{week_number}周数据已保存到: {filename}")
            except Exception as e:
                print(f"保存第{week_number}周数据失败: {e}")

def auto_process_data():
    """
    自动调用数据处理脚本
    """
    try:
        print("\n" + "=" * 60)
        print("开始自动处理数据...")
        
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        processor_script = os.path.join(current_dir, "schedule_data_processor.py")
        
        if not os.path.exists(processor_script):
            print(f"错误: 找不到数据处理脚本 {processor_script}")
            return False
        
        # 调用数据处理脚本，自动选择处理所有周数据
        print("正在调用数据处理脚本...")
        result = subprocess.run(
            [sys.executable, processor_script],
            input="2\n",  # 自动选择选项2（处理所有周汇总数据）
            text=True,
            capture_output=True,
            cwd=current_dir
        )
        
        if result.returncode == 0:
            print("数据处理完成！")
            print(result.stdout)
            return True
        else:
            print(f"数据处理失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"自动处理数据时发生错误: {e}")
        return False

def organize_output_files():
    """
    整理输出文件，将CSV和JSON文件分别存放到专门的文件夹中
    """
    try:
        print("\n开始整理输出文件...")
        current_dir = os.getcwd()
        
        # 创建输出文件夹
        csv_dir = os.path.join(current_dir, "csv_files")
        json_dir = os.path.join(current_dir, "json_files")
        
        os.makedirs(csv_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)
        
        # 移动CSV文件
        csv_files = glob.glob(os.path.join(current_dir, '*.csv'))
        moved_csv = []
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            new_path = os.path.join(csv_dir, filename)
            try:
                os.rename(file_path, new_path)
                moved_csv.append(filename)
                print(f"CSV文件已移动: {filename}")
            except Exception as e:
                print(f"移动CSV文件失败 {filename}: {e}")
        
        # 移动JSON文件
        json_files = glob.glob(os.path.join(current_dir, '*.json'))
        moved_json = []
        for file_path in json_files:
            filename = os.path.basename(file_path)
            new_path = os.path.join(json_dir, filename)
            try:
                os.rename(file_path, new_path)
                moved_json.append(filename)
                print(f"JSON文件已移动: {filename}")
            except Exception as e:
                print(f"移动JSON文件失败 {filename}: {e}")
        
        # 删除HTML响应文件
        html_files = glob.glob(os.path.join(current_dir, '*_response_*.html'))
        deleted_html = []
        for file_path in html_files:
            try:
                os.remove(file_path)
                deleted_html.append(os.path.basename(file_path))
                print(f"已删除HTML文件: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"删除HTML文件失败 {os.path.basename(file_path)}: {e}")
        
        # 输出整理结果
        print(f"\n文件整理完成:")
        print(f"  - 移动了 {len(moved_csv)} 个CSV文件到 csv_files/ 文件夹")
        print(f"  - 移动了 {len(moved_json)} 个JSON文件到 json_files/ 文件夹")
        print(f"  - 删除了 {len(deleted_html)} 个HTML响应文件")
        
        if moved_csv:
            print("\nCSV文件列表:")
            for filename in moved_csv:
                print(f"  - csv_files/{filename}")
        
        if moved_json:
            print("\nJSON文件列表:")
            for filename in moved_json:
                print(f"  - json_files/{filename}")
        
        return True
        
    except Exception as e:
        print(f"整理输出文件时发生错误: {e}")
        return False

def main():
    """
    主函数
    """
    print("所有周课表爬虫启动")
    print("=" * 60)
    
    # 创建爬虫实例
    crawler = AllWeeksScheduleCrawler()
    
    # 用户凭据（需要根据实际情况修改）
    user_no = os.getenv("xuehao")
    password = os.getenv("mima")
    
    # 默认爬取所有周的课表（22周）
    max_week = 22
    print(f"默认爬取所有周课表，最大周数: {max_week}")
    
    # 执行整个学期爬取流程
    results = crawler.crawl_all_weeks(user_no, password, max_week)
    
    # 保存原始数据
    raw_data_saved = False
    if results['all_weeks_data']:
        # 保存汇总数据
        summary_path = crawler.save_raw_data(results['all_weeks_data'])
        
        # 保存各周单独数据
        individual_paths = crawler.save_individual_week_data(results['all_weeks_data'])
        
        raw_data_saved = summary_path is not None
    
    # 输出爬取结果摘要
    print("\n" + "=" * 60)
    print("爬取结果摘要:")
    print("-" * 40)
    print(f"登录状态: {'成功' if results['login_success'] else '失败'}")
    
    if results['user_info']:
        print(f"用户姓名: {results['user_info']['name']}")
        print(f"学号: {results['user_info']['userNo']}")
        print(f"班级: {results['user_info']['clsName']}")
    
    print(f"目标周数: 1-{results['max_week']}周")
    print(f"成功获取: {len(results['success_weeks'])}周")
    
    if results['success_weeks']:
        print(f"成功周数: {results['success_weeks']}")
    
    if results['failed_weeks']:
        print(f"失败周数: {results['failed_weeks']}")
    
    if not results['all_weeks_data']:
        print("\n" + "=" * 60)
        print("❌ 数据爬取失败，无法继续处理")
        return
    
    # 如果数据爬取成功，自动处理数据
    if raw_data_saved:
        process_success = auto_process_data()
        
        if process_success:
            # 数据处理成功后，整理输出文件
            organize_success = organize_output_files()
            
            print("\n" + "=" * 60)
            print("✅ 完整流程执行完成！")
            print("-" * 40)
            print("最终输出文件:")
            print("- all_weeks_schedule_*.csv: 所有周汇总CSV文件")
            print("- schedule_data_week_*.csv: 各周单独CSV文件")
            print("- all_weeks_parsed_summary_*.json: 所有周解析数据汇总")
            print("- parsed_schedule_data_week_*.json: 各周解析后的JSON数据")
            print("\n所有中间文件已自动清理，只保留最终处理结果。")
        else:
            print("\n" + "=" * 60)
            print("⚠️  数据处理失败")
            print("原始数据文件已保存，您可以手动运行 schedule_data_processor.py 进行处理")
    else:
        print("\n" + "=" * 60)
        print("❌ 数据保存失败，无法继续处理")

if __name__ == "__main__":
    main()