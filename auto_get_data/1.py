import requests
import json
from datetime import datetime, timedelta
import time

class DeliCloudCompleteAuth:
    def __init__(self):
        self.session = requests.Session()
        self.main_token = None
        self.user_id = None
        self.attendance_token = None
        self.source_org_id = "922442506367696896" 
        self.attendance_org_id = "922442508243161088" 
        self.member_id = "46"
        self.member_name = None
        
    def step1_main_login(self):
        print("=" * 70)
        print("步骤1: 主系统登录")
        print("=" * 70)
        
        url = "https://v2-app.delicloud.com/api/v3.0/auth/web/trusted/login"
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "client_id": "eplus_web",
            "content-type": "application/json",
            "host": "v2-app.delicloud.com",
            "origin": "https://v2-web.delicloud.com",
            "referer": "https://v2-web.delicloud.com/",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
            "x-service-id": "userauth"
        }
        
        payload = {
            "mobile": "13173689200",
            "password": "==AMwITO4YzM3EzMxQHa",
            "trust_code": "jg5y2tFWfNVTIOEV"
        }
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在登录主系统...")
        print(f"URL: {url}")
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                data = result.get("data", {})
                self.main_token = data.get('token')
                self.user_id = data.get('user_id')
                
                print(f"[✓] 主系统登录成功！")
                print(f"  Token (64位): {self.main_token[:50]}...")
                print(f"  Token长度: {len(self.main_token)}位")
                print(f"  用户ID: {self.user_id}")
                
                return True
            else:
                print(f"[✗] 主系统登录失败: {result.get('msg')}")
                return False
                
        except Exception as e:
            print(f"[✗] 请求失败: {e}")
            return False
    
    def step2_attendance_login(self):
        """
        步骤2: 考勤系统登录
        使用主系统token获取32位考勤token
        """
        if not self.main_token:
            print("[!] 请先完成主系统登录")
            return False
        
        print("\n" + "=" * 70)
        print("步骤2: 考勤系统登录（Token交换）")
        print("=" * 70)
        
        url = "https://checkin2-app.delicloud.com/api/v2.0/auth/login"
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "client_id": "eplus_web",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://v2-eapp.delicloud.com",
            "pragma": "no-cache",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
            "x-service-id": "auth"
        }
        
        payload = {
            "sourceId": "deli",
            "orgId": self.source_org_id,
            "sourceToken": self.main_token,
            "memberId": self.member_id
        }
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在登录考勤系统...")
        print(f"URL: {url}")
        print(f"Payload:")
        print(f"  sourceId: {payload['sourceId']}")
        print(f"  orgId: {payload['orgId']}")
        print(f"  sourceToken: {payload['sourceToken'][:50]}...")
        print(f"  memberId: {payload['memberId']}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 0:
                    data = result.get("data", {})
                    
                    self.attendance_token = data.get("token")
                    expire_ms = data.get("expire", "86400000")
                    expire_hours = int(expire_ms) / 1000 / 3600
                    
                    member_infos = data.get("member_infos", [])
                    if member_infos:
                        self.attendance_org_id = member_infos[0].get("org_id")
                        self.member_id = str(member_infos[0].get("user_id"))
                    
                    extra_data = data.get("extra_data", {})
                    self.member_name = extra_data.get("name", "")
                    
                    print(f"\n[✓✓✓] 考勤系统登录成功！")
                    print(f"  考勤Token (32位): {self.attendance_token}")
                    print(f"  Token长度: {len(self.attendance_token)}位")
                    print(f"  过期时间: {expire_hours:.1f}小时")
                    print(f"  用户名: {self.member_name}")
                    print(f"  成员ID: {self.member_id}")
                    print(f"  组织ID: {self.attendance_org_id}")
                    
                    with open("attendance_login_response.json", "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    return True
                else:
                    print(f"[✗] 考勤登录失败: {result.get('msg')}")
                    return False
            else:
                print(f"[✗] HTTP错误: {response.status_code}")
                try:
                    print(f"响应内容: {response.text[:200]}")
                except:
                    pass
                return False
                
        except Exception as e:
            print(f"[✗] 请求失败: {e}")
            return False
    
    def step3_test_attendance_api(self):
        """
        步骤3: 测试考勤API
        使用获得的32位token访问考勤数据
        """
        if not self.attendance_token:
            print("[!] 请先完成考勤系统登录")
            return False
        
        print("\n" + "=" * 70)
        print("步骤3: 测试考勤API访问")
        print("=" * 70)
        
        url = "https://checkin2-app.delicloud.com/api/v2.0/integration/record/search"
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "authorization": self.attendance_token,
            "cache-control": "no-cache",
            "client_id": "eplus_web",
            "content-type": "application/json;charset=UTF-8",
            "member_id": self.member_id,
            "org_id": self.attendance_org_id,
            "origin": "https://v2-eapp.delicloud.com",
            "pragma": "no-cache",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
            "x-service-id": "ass-integration"
        }
        
        today = datetime.now()
        start_time = int(today.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        end_time = int(today.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)
        
        payload = {
            "org_id": self.attendance_org_id,
            "page": 1,
            "size": 100,
            "start_time": start_time,
            "end_time": end_time,
            "dept_ids": [],
            "member_ids": [],
            "order": 0,
            "checkin_time_order": 0
        }
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 请求考勤数据...")
        print(f"使用Token: {self.attendance_token}")
        print(f"组织ID: {self.attendance_org_id}")
        print(f"日期范围: {today.strftime('%Y-%m-%d')} 00:00:00 - 23:59:59")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("code") == 0:
                    total = result.get("data", {}).get("total", 0)
                    rows = result.get("data", {}).get("rows", [])
                    
                    print(f"\n[✓] 考勤数据获取成功！")
                    print(f"总记录数: {total}")
                    
                    if rows:
                        print("\n今日考勤记录:")
                        print("-" * 50)
                        
                        person_records = {}
                        for row in rows:
                            name = row.get("member_name", "未知")
                            if name not in person_records:
                                person_records[name] = []
                            
                            timestamp = int(row["check_in_time"]) / 1000
                            check_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                            device = row.get("checkin_extra_data", {}).get("device_name", "")
                            
                            person_records[name].append({
                                "time": check_time,
                                "device": device
                            })
                        
                        for name, records in person_records.items():
                            print(f"\n【{name}】({len(records)}次)")
                            for record in sorted(records, key=lambda x: x["time"]):
                                print(f"  • {record['time']} - {record['device']}")
                    else:
                        print("\n今日暂无考勤记录")
                    
                    with open(f"attendance_data_{today.strftime('%Y%m%d')}.json", "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f"\n完整数据已保存到 attendance_data_{today.strftime('%Y%m%d')}.json")
                    
                    return True
                else:
                    print(f"[✗] 业务错误: {result.get('msg')}")
                    return False
            else:
                print(f"[✗] HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[✗] 请求失败: {e}")
            return False
    
    def run_complete_flow(self):
        """运行完整的认证流程"""
        print("=" * 70)
        print("得力云完整认证流程")
        print("=" * 70)
        print("\n流程说明:")
        print("1. 主系统登录 → 获取64位token")
        print("2. 考勤系统登录 → 用64位token交换32位token")
        print("3. 访问考勤API → 使用32位token获取数据")
        print("=" * 70)
        
        if not self.step1_main_login():
            print("\n[✗] 流程中断：主系统登录失败")
            return
        
        time.sleep(1)
        
        if not self.step2_attendance_login():
            print("\n[✗] 流程中断：考勤系统登录失败")
            return
        
        time.sleep(1)
        
        if self.step3_test_attendance_api():
            print("\n" + "=" * 70)
            print("[✓✓✓] 完整流程执行成功！")
            print("=" * 70)
            print("\n认证信息汇总:")
            print(f"  主系统Token: {self.main_token[:40]}... (64位)")
            print(f"  考勤Token: {self.attendance_token} (32位)")
            print(f"  用户: {self.member_name}")
            print(f"  成员ID: {self.member_id}")
            print(f"  源组织ID: {self.source_org_id}")
            print(f"  考勤组织ID: {self.attendance_org_id}")
            
            auth_info = {
                "main_system": {
                    "token": self.main_token,
                    "user_id": self.user_id
                },
                "attendance_system": {
                    "token": self.attendance_token,
                    "member_id": self.member_id,
                    "member_name": self.member_name,
                    "source_org_id": self.source_org_id,
                    "attendance_org_id": self.attendance_org_id
                },
                "timestamp": datetime.now().isoformat()
            }
            
            with open("complete_auth_info.json", "w", encoding="utf-8") as f:
                json.dump(auth_info, f, ensure_ascii=False, indent=2)
            
            print("\n所有认证信息已保存到 complete_auth_info.json")
        else:
            print("\n[✗] 考勤数据获取失败")


def main():
    client = DeliCloudCompleteAuth()
    client.run_complete_flow()


if __name__ == "__main__":
    main()