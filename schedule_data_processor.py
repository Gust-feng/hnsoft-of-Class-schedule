#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课表数据处理脚本
专门用于处理爬虫获得的原始课表数据，将其转换为可读格式并导出
"""

import json
import csv
import os
from datetime import datetime
import glob
import re

class ScheduleDataProcessor:
    """
    课表数据处理类
    """
    
    def __init__(self):
        self.weekday_map = {
            '1': '星期一', '2': '星期二', '3': '星期三', 
            '4': '星期四', '5': '星期五', '6': '星期六', '7': '星期日'
        }
        self.week_dates = {}  # 存储每周的日期信息
    
    def load_json_data(self, filepath):
        """
        加载JSON数据文件
        
        Args:
            filepath (str): JSON文件路径
            
        Returns:
            dict: 加载的数据
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"成功加载数据文件: {filepath}")
            return data
        except Exception as e:
            print(f"加载数据文件失败 {filepath}: {e}")
            return None
    
    def extract_dates_from_html_responses(self, directory="."):
        """
        从HTML响应文件中提取日期信息
        
        Args:
            directory (str): 搜索目录
            
        Returns:
            dict: 每周的日期信息 {week_number: {weekday: date}}
        """
        print("\n正在从HTML响应文件中提取日期信息...")
        
        # 查找所有周的响应文件
        pattern = os.path.join(directory, "*schedule_data_week*_response_*.html")
        html_files = glob.glob(pattern)
        
        week_dates = {}
        
        for html_file in html_files:
            try:
                # 从文件名中提取周数
                filename = os.path.basename(html_file)
                week_match = re.search(r'week(\d+)_response', filename)
                if not week_match:
                    continue
                
                week_number = week_match.group(1)
                
                # 读取HTML文件内容（实际是JSON）
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # 解析JSON内容
                data = json.loads(content)
                
                # 提取日期信息
                if 'data' in data and data['data']:
                    week_data = data['data'][0] if isinstance(data['data'], list) else data['data']
                    if 'date' in week_data:
                        dates = {}
                        for date_info in week_data['date']:
                            xqid = date_info.get('xqid', '')  # 星期ID (0-6, 0是星期日)
                            date_str = date_info.get('mxrq', '')
                            
                            if xqid and date_str:
                                # 将xqid转换为weekDay格式 (1-7, 7是星期日)
                                # xqid: 0=星期日, 1=星期一, ..., 6=星期六
                                # weekDay: 1=星期一, 2=星期二, ..., 7=星期日
                                if xqid == '0':
                                    weekday = '7'  # 星期日
                                else:
                                    weekday = xqid  # 星期一到星期六保持不变
                                
                                dates[weekday] = date_str
                        
                        if dates:
                            week_dates[week_number] = dates
                            print(f"  第{week_number}周: {len(dates)}个日期")
                
            except Exception as e:
                print(f"处理文件 {html_file} 时出错: {e}")
                continue
        
        self.week_dates = week_dates
        print(f"成功提取 {len(week_dates)} 周的日期信息")
        return week_dates
    
    def _get_course_date(self, week_number, weekday):
        """
        获取课程的真实日期
        
        Args:
            week_number (str): 周数
            weekday (str): 星期几 (1-7)
            
        Returns:
            str: 日期字符串，如果找不到则返回当前日期
        """
        print(f"DEBUG: _get_course_date调用 - week_number: {week_number}, weekday: {weekday}")
        print(f"DEBUG: self.week_dates内容: {self.week_dates}")
        
        # 如果week_number是'raw'，尝试使用当前周的周数
        actual_week_number = week_number
        if week_number == 'raw':
            # 从self.week_dates中找到第一个可用的周数
            if self.week_dates:
                actual_week_number = list(self.week_dates.keys())[0]
                print(f"DEBUG: Converting 'raw' to week {actual_week_number}")
        
        if actual_week_number and weekday and actual_week_number in self.week_dates:
            week_dates = self.week_dates[actual_week_number]
            print(f"DEBUG: 找到周{actual_week_number}的日期数据: {week_dates}")
            if weekday in week_dates:
                real_date = week_dates[weekday]
                print(f"DEBUG: 找到星期{weekday}的真实日期: {real_date}")
                return real_date
            else:
                print(f"DEBUG: 在周{actual_week_number}的日期数据中未找到星期{weekday}")
        else:
            print(f"DEBUG: 未找到周{actual_week_number}的日期数据或参数为空")
        
        # 如果找不到真实日期，返回当前日期
        current_date = datetime.now().strftime("%Y-%m-%d")
        print(f"DEBUG: 返回当前日期: {current_date}")
        return current_date
    
    def _extract_dates_from_json(self, json_filepath):
        """
        从JSON数据中提取日期信息
        
        Args:
            json_filepath (str): JSON文件路径
        """
        try:
            # 加载JSON数据
            raw_data = self.load_json_data(json_filepath)
            if not raw_data or 'data' not in raw_data:
                return
            
            data = raw_data['data']
            if not isinstance(data, list) or len(data) == 0:
                return
            
            week_data = data[0]
            if 'date' not in week_data:
                return
            
            # 提取周数
            week_number = None
            if week_data.get('date') and len(week_data['date']) > 0:
                week_number = week_data['date'][0].get('zc')
            
            if not week_number:
                return
            
            # 提取日期信息
            dates = {}
            for date_info in week_data['date']:
                xqid = date_info.get('xqid', '')  # 星期ID (0-6, 0是星期日)
                date_str = date_info.get('mxrq', '')
                
                if xqid and date_str:
                    # 转换xqid为weekDay格式 (1-7, 7是星期日)
                    if xqid == "0":
                        weekday = "7"  # 星期日
                    else:
                        weekday = xqid
                    
                    dates[weekday] = date_str
            
            if dates:
                self.week_dates = {week_number: dates}
                print(f"从JSON数据中成功提取第{week_number}周的日期信息")
                print(f"日期映射: {dates}")
            else:
                print("未能从JSON数据中提取到日期信息")
            
        except Exception as e:
            print(f"从JSON数据中提取日期信息时出错: {e}")
     
    def parse_course_data(self, course_data):
        """
        解析课程表数据为可读格式
        
        Args:
            course_data (dict): 课程表JSON数据
            
        Returns:
            dict: 解析后的可读数据
        """
        if not course_data or 'data' not in course_data:
            return None
            
        parsed_data = {
            'success': course_data.get('code') == '1' or course_data.get('code') == 1,
            'message': course_data.get('Msg', course_data.get('msg', '')),
            'semester_info': {},
            'courses': [],
            'weekly_schedule': {},
            'time_slots': []
        }
        
        data = course_data['data'][0] if isinstance(course_data['data'], list) else course_data['data']
        
        # 解析学期信息
        if 'topInfo' in data and data['topInfo']:
            top_info = data['topInfo'][0]
            parsed_data['semester_info'] = {
                'semester_id': top_info.get('semesterId', ''),
                'current_week': top_info.get('week', ''),
                'today': top_info.get('today', ''),
                'weekday': top_info.get('weekday', ''),
                'max_week': top_info.get('maxWeek', '')
            }
        
        # 解析时间节次
        if 'nodesLst' in data:
            parsed_data['time_slots'] = [
                {
                    'node_number': node.get('nodeNumber', ''),
                    'node_name': node.get('nodeName', '')
                }
                for node in data['nodesLst']
            ]
        
        # 解析课程信息（只使用courses数组，避免与item数组重复）
        if 'courses' in data:
            # 初始化每周课程安排
            weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            weekday_map = {'1': '周一', '2': '周二', '3': '周三', '4': '周四', '5': '周五', '6': '周六', '7': '周日', '0': '周日'}
            
            for weekday in weekdays:
                parsed_data['weekly_schedule'][weekday] = []
            
            for course in data['courses']:
                parsed_course = {
                    'course_name': course.get('courseName', ''),
                    'teacher_name': course.get('teacherName', ''),
                    'class_name': course.get('ktmc', ''),
                    'classroom': course.get('classroomName', ''),
                    'location': course.get('location', ''),
                    'building': course.get('buildingName', ''),
                    'week_day': course.get('weekDay', ''),
                    'class_week': course.get('classWeek', ''),
                    'class_time': course.get('classTime', ''),
                    'start_time': course.get('startTime', ''),
                    'end_time': course.get('endTIme', ''),
                    'exam_type': course.get('khfs', ''),
                    'student_count': course.get('xkrs', 0),
                    'course_notes': course.get('coursesNote', 0),
                    'week_details': course.get('classWeekDetails', '').strip(',').split(',') if course.get('classWeekDetails') else []
                }
                parsed_data['courses'].append(parsed_course)
                
                # 同时将课程添加到对应的星期安排中
                week_day = course.get('weekDay', '')
                weekday_name = weekday_map.get(week_day, '')
                if weekday_name:
                    weekly_course = {
                        'course_name': course.get('courseName', ''),
                        'teacher_name': course.get('teacherName', ''),
                        'classroom': course.get('classroomName', ''),
                        'start_time': course.get('startTime', ''),
                        'end_time': course.get('endTIme', ''),
                        'class_week': course.get('classWeek', '')
                    }
                    parsed_data['weekly_schedule'][weekday_name].append(weekly_course)
        
        return parsed_data
    
    def save_parsed_data(self, parsed_data, week_number=None, output_dir="."):
        """
        保存解析后的数据到JSON文件
        
        Args:
            parsed_data (dict): 解析后的数据
            week_number (str): 周数
            output_dir (str): 输出目录
        """
        # 创建JSON文件夹
        json_dir = os.path.join(output_dir, "json_files")
        os.makedirs(json_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        week_suffix = f"_week{week_number}" if week_number else ""
        filename = f"parsed_schedule_data{week_suffix}_{timestamp}.json"
        filepath = os.path.join(json_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)
            print(f"解析后的数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            print(f"保存解析数据失败: {e}")
            return None
    
    def save_to_csv(self, parsed_data, week_number=None, output_dir="."):
        """
        保存数据到CSV文件
        
        Args:
            parsed_data (dict): 解析后的数据
            week_number (str): 周数
            output_dir (str): 输出目录
        """
        # 创建CSV文件夹
        csv_dir = os.path.join(output_dir, "csv_files")
        os.makedirs(csv_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        week_suffix = f"_week{week_number}" if week_number else ""
        filename = f"课表{week_suffix}_{timestamp}.csv"
        filepath = os.path.join(csv_dir, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['日期', '星期', '节次', '开始时间', '结束时间', '课程名称', '教师', '教室', '教学周', '考试类型', '学生人数', '班级']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # 写入表头
                writer.writeheader()
                
                # 写入课程数据
                for course in parsed_data.get('courses', []):
                    # 格式化星期信息
                    weekday = self.weekday_map.get(course.get('week_day', ''), f"星期{course.get('week_day', '')}")
                    
                    # 获取真实日期信息
                    course_date = self._get_course_date(week_number, course.get('week_day', ''))
                    
                    # 格式化节次信息
                    class_time = course.get('class_time', '')
                    if class_time:
                        # 将节次数字转换为更易读的格式
                        class_time_formatted = f"第{class_time}节"
                    else:
                        class_time_formatted = ''
                    
                    writer.writerow({
                        '日期': course_date,
                        '星期': weekday,
                        '节次': class_time_formatted,
                        '开始时间': course.get('start_time', ''),
                        '结束时间': course.get('end_time', ''),
                        '课程名称': course.get('course_name', ''),
                        '教师': course.get('teacher_name', ''),
                        '教室': course.get('location', '') or course.get('classroom', ''),
                        '教学周': course.get('class_week', ''),
                        '考试类型': course.get('exam_type', ''),
                        '学生人数': course.get('student_count', ''),
                        '班级': course.get('class_name', '')
                    })
            
            print(f"CSV数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            print(f"保存CSV数据失败: {e}")
            return None
    
    def save_all_weeks_csv(self, all_weeks_data, output_dir="."):
        """
        保存所有周的课程表数据到CSV文件
        
        Args:
            all_weeks_data (dict): 所有周的解析数据
            output_dir (str): 输出目录
        """
        # 创建CSV文件夹
        csv_dir = os.path.join(output_dir, "csv_files")
        os.makedirs(csv_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"课表_all_weeks_{timestamp}.csv"
        filepath = os.path.join(csv_dir, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['生成日期', '周次', '星期', '节次', '开始时间', '结束时间', '课程名称', '教师', '教室', '教学周', '考试类型', '学生人数', '班级']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # 写入表头
                writer.writeheader()
                
                # 遍历所有周的数据
                for week_key, parsed_data in all_weeks_data.items():
                    if isinstance(parsed_data, dict) and 'courses' in parsed_data:
                        week_number = week_key.replace('week_', '')
                        
                        for course in parsed_data.get('courses', []):
                            # 格式化星期信息
                            weekday = self.weekday_map.get(course.get('week_day', ''), f"星期{course.get('week_day', '')}")
                            
                            # 获取真实日期信息
                            course_date = self._get_course_date(week_number, course.get('week_day', ''))
                            
                            # 格式化节次信息
                            class_time = course.get('class_time', '')
                            if class_time:
                                # 将节次数字转换为更易读的格式
                                class_time_formatted = f"第{class_time}节"
                            else:
                                class_time_formatted = ''
                            
                            writer.writerow({
                                '生成日期': course_date,
                                '周次': f"第{week_number}周",
                                '星期': weekday,
                                '节次': class_time_formatted,
                                '开始时间': course.get('start_time', ''),
                                '结束时间': course.get('end_time', ''),
                                '课程名称': course.get('course_name', ''),
                                '教师': course.get('teacher_name', ''),
                                '教室': course.get('location', '') or course.get('classroom', ''),
                                '教学周': course.get('class_week', ''),
                                '考试类型': course.get('exam_type', ''),
                                '学生人数': course.get('student_count', ''),
                                '班级': course.get('class_name', '')
                            })
            
            print(f"所有周CSV数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            print(f"保存所有周CSV数据失败: {e}")
            return None
    
    def print_course_summary(self, parsed_data, week_number=None):
        """
        打印课程表摘要信息
        
        Args:
            parsed_data (dict): 解析后的数据
            week_number (str): 周数
        """
        if not parsed_data:
            print("无有效数据")
            return
            
        week_title = f"第{week_number}周" if week_number else "当前"
        print(f"\n{week_title}课程表摘要:")
        print("-" * 50)
        
        # 学期信息
        if parsed_data['semester_info']:
            info = parsed_data['semester_info']
            print(f"学期: {info.get('semester_id', 'N/A')}")
            print(f"当前周: {info.get('current_week', 'N/A')}")
            print(f"最大周数: {info.get('max_week', 'N/A')}")
            print(f"今天: {info.get('today', 'N/A')} ({info.get('weekday', 'N/A')})")
        
        # 课程统计
        print(f"\n课程总数: {len(parsed_data['courses'])}")
        
        # 按课程名称分组统计
        course_count = {}
        for course in parsed_data['courses']:
            name = course['course_name']
            if name in course_count:
                course_count[name] += 1
            else:
                course_count[name] = 1
        
        print("\n课程列表:")
        for course_name, count in course_count.items():
            print(f"  - {course_name}: {count}节课")
        
        # 每日课程安排
        print("\n每日课程安排:")
        for weekday, courses in parsed_data['weekly_schedule'].items():
            if courses:
                print(f"  {weekday}: {len(courses)}节课")
                for course in courses:
                    print(f"    - {course['course_name']} ({course['start_time']}-{course['end_time']}) - {course['teacher_name']}")
            else:
                print(f"  {weekday}: 无课程")
        
        print("-" * 50)
    
    def process_single_week_data(self, json_filepath, output_dir="."):
        """
        处理单周数据
        
        Args:
            json_filepath (str): JSON文件路径
            output_dir (str): 输出目录
            
        Returns:
            dict: 处理结果
        """
        print(f"\n处理单周数据: {json_filepath}")
        
        # 尝试提取日期信息
        self.extract_dates_from_html_responses(output_dir)
        
        # 如果没有提取到日期信息，尝试从JSON数据中提取
        if not self.week_dates:
            print("未找到HTML响应文件，尝试从JSON数据中提取日期信息...")
            self._extract_dates_from_json(json_filepath)
        
        # 加载原始数据
        raw_data = self.load_json_data(json_filepath)
        if not raw_data:
            return None
        
        # 从文件名中提取周数
        filename = os.path.basename(json_filepath)
        week_number = None
        if 'week_' in filename:
            try:
                week_part = filename.split('week_')[1].split('_')[0]
                week_number = week_part
            except:
                pass
        elif 'current_week' in filename:
            # 对于当前周数据，从JSON内容中提取周数
            if raw_data and 'data' in raw_data and len(raw_data['data']) > 0:
                week_data = raw_data['data'][0]
                if 'topInfo' in week_data and len(week_data['topInfo']) > 0:
                    week_number = week_data['topInfo'][0].get('week')
                elif 'date' in week_data and len(week_data['date']) > 0:
                    week_number = week_data['date'][0].get('zc')
            print(f"从当前周数据中提取到周数: {week_number}")
        
        # 解析数据
        parsed_data = self.parse_course_data(raw_data)
        if not parsed_data:
            print("数据解析失败")
            return None
        
        # 保存解析后的数据（仅CSV格式）
        csv_path = self.save_to_csv(parsed_data, week_number, output_dir)
        
        # 打印摘要
        self.print_course_summary(parsed_data, week_number)
        
        return {
            'week_number': week_number,
            'parsed_data': parsed_data,
            'csv_path': csv_path
        }
    
    def process_all_weeks_data(self, json_filepath, output_dir="."):
        """
        处理所有周数据
        
        Args:
            json_filepath (str): JSON文件路径
            output_dir (str): 输出目录
            
        Returns:
            dict: 处理结果
        """
        print(f"\n处理所有周数据: {json_filepath}")
        
        # 提取日期信息
        self.extract_dates_from_html_responses(output_dir)
        
        # 加载原始数据
        raw_data = self.load_json_data(json_filepath)
        if not raw_data:
            return None
        
        all_weeks_parsed = {}
        results = {
            'total_weeks': 0,
            'success_weeks': 0,
            'failed_weeks': [],
            'parsed_data': {},
            'json_paths': [],
            'csv_paths': []
        }
        
        # 处理每周数据
        for week_key, week_data in raw_data.items():
            if week_key.startswith('week_'):
                week_number = week_key.replace('week_', '')
                results['total_weeks'] += 1
                
                print(f"\n处理第{week_number}周数据...")
                
                # 解析数据
                parsed_data = self.parse_course_data(week_data)
                if parsed_data:
                    all_weeks_parsed[week_key] = parsed_data
                    results['success_weeks'] += 1
                    
                    # 保存单周数据（仅CSV格式）
                    csv_path = self.save_to_csv(parsed_data, week_number, output_dir)
                    
                    if csv_path:
                        results['csv_paths'].append(csv_path)
                    
                    # 打印摘要
                    self.print_course_summary(parsed_data, week_number)
                else:
                    results['failed_weeks'].append(week_number)
                    print(f"第{week_number}周数据解析失败")
        
        # 保存所有周的汇总数据（仅CSV格式）
        if all_weeks_parsed:
            results['parsed_data'] = all_weeks_parsed
            
            # 保存汇总CSV
            csv_summary_path = self.save_all_weeks_csv(all_weeks_parsed, output_dir)
            if csv_summary_path:
                results['summary_csv_path'] = csv_summary_path
        
        return results
    
    def find_data_files(self, directory=".", pattern="*raw_data*.json"):
        """
        查找数据文件
        
        Args:
            directory (str): 搜索目录
            pattern (str): 文件模式
            
        Returns:
            list: 找到的文件列表
        """
        search_pattern = os.path.join(directory, pattern)
        files = glob.glob(search_pattern)
        return sorted(files)

def main():
    """
    主函数
    """
    print("课表数据处理器启动")
    print("=" * 60)
    
    processor = ScheduleDataProcessor()
    
    # 查找可用的数据文件
    print("\n查找可用的数据文件...")
    current_week_files = processor.find_data_files(pattern="*current_week_raw_data*.json")
    all_weeks_files = processor.find_data_files(pattern="*all_weeks_raw_data*.json")
    individual_week_files = processor.find_data_files(pattern="week_*_raw_data*.json")
    
    print(f"找到当前周数据文件: {len(current_week_files)}个")
    print(f"找到所有周汇总数据文件: {len(all_weeks_files)}个")
    print(f"找到单独周数据文件: {len(individual_week_files)}个")
    
    if not (current_week_files or all_weeks_files or individual_week_files):
        print("\n未找到任何数据文件！")
        print("请确保已运行爬虫脚本并生成了数据文件。")
        return
    
    # 显示处理选项
    print("\n选择处理模式:")
    options = []
    
    if current_week_files:
        print(f"1. 处理当前周数据 ({len(current_week_files)}个文件)")
        options.append(('current', current_week_files))
    
    if all_weeks_files:
        print(f"2. 处理所有周汇总数据 ({len(all_weeks_files)}个文件)")
        options.append(('all', all_weeks_files))
    
    if individual_week_files:
        print(f"3. 处理单独周数据 ({len(individual_week_files)}个文件)")
        options.append(('individual', individual_week_files))
    
    print("4. 处理所有找到的数据文件")
    
    try:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1" and current_week_files:
            # 处理当前周数据
            for filepath in current_week_files:
                processor.process_single_week_data(filepath)
        
        elif choice == "2" and all_weeks_files:
            # 处理所有周汇总数据
            for filepath in all_weeks_files:
                result = processor.process_all_weeks_data(filepath)
                if result:
                    print(f"\n处理完成: 总共{result['total_weeks']}周，成功{result['success_weeks']}周")
                    if result['failed_weeks']:
                        print(f"失败周数: {result['failed_weeks']}")
        
        elif choice == "3" and individual_week_files:
            # 处理单独周数据
            for filepath in individual_week_files:
                processor.process_single_week_data(filepath)
        
        elif choice == "4":
            # 处理所有数据文件
            print("\n开始处理所有数据文件...")
            
            # 处理当前周数据
            for filepath in current_week_files:
                processor.process_single_week_data(filepath)
            
            # 处理所有周汇总数据
            for filepath in all_weeks_files:
                result = processor.process_all_weeks_data(filepath)
                if result:
                    print(f"\n处理完成: 总共{result['total_weeks']}周，成功{result['success_weeks']}周")
                    if result['failed_weeks']:
                        print(f"失败周数: {result['failed_weeks']}")
            
            # 处理单独周数据
            for filepath in individual_week_files:
                processor.process_single_week_data(filepath)
        
        else:
            print("无效选择或无对应数据文件")
            return
    
    except KeyboardInterrupt:
        print("\n用户取消操作")
        return
    except Exception as e:
        print(f"\n处理过程中发生错误: {e}")
        return
    
    print("\n" + "=" * 60)
    print("数据处理完成！")
    print("\n输出文件说明:")
    print("- parsed_schedule_data_*.json: 解析后的可读JSON数据")
    print("- schedule_data_*.csv: CSV格式课程表数据")
    print("- all_weeks_parsed_summary_*.json: 所有周解析数据汇总")
    print("- all_weeks_schedule_*.csv: 所有周CSV汇总数据")

if __name__ == "__main__":
    main()