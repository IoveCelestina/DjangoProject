# attendance/attendance_client.py
import os
import ssl
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter


class AttendanceClientError(Exception):
    """第三方考勤客户端错误（网络/鉴权/业务 code 非0 等）"""


@dataclass
class AttendanceTokens:
    main_token: str
    attendance_token: str
    attendance_token_expire: Optional[int] = None  # 秒级时间戳（如果返回）


class SSLAdapter(HTTPAdapter):
    """适配器类，强制使用 TLSv1.2 或更高版本"""

    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('TLS_AES_128_GCM_SHA256')  # 强制使用 TLSv1.2 或 TLSv1.3 加密套件
        context.set_protocol_version(ssl.PROTOCOL_TLSv1_2)  # 强制使用 TLSv1.2 协议
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


class AttendanceClient:
    def __init__(self, base_url: str = "https://center.deli.com", timeout: int = 20,
                 session: Optional[requests.Session] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

        # 使用自定义的 SSLAdapter 强制使用 TLS 1.2
        adapter = SSLAdapter()
        self.session.mount("https://", adapter)  # 强制所有 HTTPS 请求使用 TLS 1.2 协议

    def _post(self, path: str, json_body: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.post(url, json=json_body, headers=headers or {}, timeout=self.timeout)
            resp.raise_for_status()  # 如果状态码不是 200，抛出异常
            data = resp.json()
        except requests.exceptions.RequestException as e:
            raise AttendanceClientError(f"请求失败: {e}")

        # 处理接口返回的错误
        if isinstance(data, dict) and data.get("code") not in (0, "0", None):
            raise AttendanceClientError(f"接口返回失败：code={data.get('code')} msg={data.get('msg')}")
        return data



    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _require_env(name: str) -> str:
        val = os.getenv(name, "").strip()
        if not val:
            raise AttendanceClientError(f"缺少环境变量：{name}")
        return val

    def login_main(self, trust_code: str) -> str:
        """
        第一步：主系统 trusted/login 获取 64位 token
        mobile/password 建议从环境变量读取，避免前端传递与落库
        """
        mobile = self._require_env("DELI_MOBILE")
        password = self._require_env("DELI_PASSWORD")

        payload = {
            "client_id": "i",
            "client_type": "i",
            "login_type": "pw",
            "mobile": mobile,
            "password": password,
            "security_score": "",
            "trusted_code": trust_code,
        }
        data = self._post("/api/c/uc/trusted/login", payload)
        print("Login response:", data)  # 打印返回数据
        token = (data.get("data") or {}).get("token")
        if not token:
            raise AttendanceClientError("主系统登录成功但未返回 token")
        return token

    def exchange_attendance_token(self, main_token: str, source_org_id: str, attendance_org_id: str, member_id: str) -> AttendanceTokens:
        """
        第二步：用主系统 token 换考勤 token（32位）
        注意：source_org_id / attendance_org_id / member_id 来自你业务配置
        """
        headers = {"Authorization": main_token}
        payload = {
            "source_org_id": source_org_id,
            "attendance_org_id": attendance_org_id,
            "member_id": member_id,
        }
        data = self._post("/api/attendance/uc/token", payload, headers=headers)
        token_data = data.get("data") or {}
        attendance_token = token_data.get("token")
        expire = token_data.get("expire")
        if not attendance_token:
            raise AttendanceClientError("换取考勤 token 成功但未返回 token")
        return AttendanceTokens(main_token=main_token, attendance_token=attendance_token, attendance_token_expire=expire)

    def fetch_records_page(
        self,
        attendance_token: str,
        source_org_id: str,
        attendance_org_id: str,
        member_id: str,
        start_time_ms: int,
        end_time_ms: int,
        page: int = 1,
        size: int = 100,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        第三步：拉取考勤 record/search 单页
        返回：(rows, total)
        """
        headers = {"Authorization": attendance_token}
        payload = {
            "source_org_id": source_org_id,
            "attendance_org_id": attendance_org_id,
            "member_id": member_id,
            "start_time": start_time_ms,
            "end_time": end_time_ms,
            "keyword": "",
            "dept_id": None,
            "page": page,
            "size": size,
        }
        data = self._post("/api/attendance/integration/record/search", payload, headers=headers)
        d = data.get("data") or {}
        rows = d.get("rows") or []
        total = int(d.get("total") or 0)
        if not isinstance(rows, list):
            raise AttendanceClientError("record/search 返回 rows 非列表")
        return rows, total

    def fetch_records_all(
        self,
        attendance_token: str,
        source_org_id: str,
        attendance_org_id: str,
        member_id: str,
        start_time_ms: int,
        end_time_ms: int,
        size: int = 100,
        max_pages: int = 2000,
    ) -> List[Dict[str, Any]]:
        """
        拉取指定时间范围内所有 records（自动翻页）
        - max_pages 防止第三方接口异常导致死循环
        """
        all_rows: List[Dict[str, Any]] = []
        page = 1
        total = 0

        while page <= max_pages:
            rows, total = self.fetch_records_page(
                attendance_token=attendance_token,
                source_org_id=source_org_id,
                attendance_org_id=attendance_org_id,
                member_id=member_id,
                start_time_ms=start_time_ms,
                end_time_ms=end_time_ms,
                page=page,
                size=size,
            )
            all_rows.extend(rows)

            # 结束条件：已取完或该页为空
            if not rows:
                break
            if total and len(all_rows) >= total:
                break

            page += 1

        return all_rows
# attendance/attendance_client.py
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests


class AttendanceClientError(Exception):
    """第三方考勤客户端错误（网络/鉴权/业务 code 非0 等）"""


@dataclass
class AttendanceTokens:
    main_token: str
    attendance_token: str
    attendance_token_expire: Optional[int] = None  # 秒级时间戳（如果返回）


class AttendanceClient:
    """
    第三方考勤接口客户端（封装 HTTP 调用）
    - 只负责：登录/换 token/拉取 record/search
    - 不负责：落库、计算、回写
    """

    def __init__(
        self,
        base_url: str = "https://center.deli.com",
        timeout: int = 20,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def _post(self, path: str, json_body: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        resp = self.session.post(url, json=json_body, headers=headers or {}, timeout=self.timeout)
        if resp.status_code != 200:
            raise AttendanceClientError(f"HTTP {resp.status_code} 调用失败：{path}")
        data = resp.json()
        # 第三方接口普遍使用 code/msg
        if isinstance(data, dict) and data.get("code") not in (0, "0", None):
            # 不打印敏感字段
            raise AttendanceClientError(f"接口返回失败：{path} code={data.get('code')} msg={data.get('msg')}")
        return data

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _require_env(name: str) -> str:
        val = os.getenv(name, "").strip()
        if not val:
            raise AttendanceClientError(f"缺少环境变量：{name}")
        return val

    def login_main(self, trust_code: str) -> str:
        """
        第一步：主系统 trusted/login 获取 64位 token
        mobile/password 建议从环境变量读取，避免前端传递与落库
        """
        mobile = self._require_env("DELI_MOBILE")
        password = self._require_env("DELI_PASSWORD")

        payload = {
            "client_id": "i",
            "client_type": "i",
            "login_type": "pw",
            "mobile": mobile,
            "password": password,
            "security_score": "",
            "trusted_code": trust_code,
        }
        data = self._post("/api/c/uc/trusted/login", payload)
        token = (data.get("data") or {}).get("token")
        if not token:
            raise AttendanceClientError("主系统登录成功但未返回 token")
        return token

    def exchange_attendance_token(self, main_token: str, source_org_id: str, attendance_org_id: str, member_id: str) -> AttendanceTokens:
        """
        第二步：用主系统 token 换考勤 token（32位）
        注意：source_org_id / attendance_org_id / member_id 来自你业务配置
        """
        headers = {"Authorization": main_token}
        payload = {
            "source_org_id": source_org_id,
            "attendance_org_id": attendance_org_id,
            "member_id": member_id,
        }
        data = self._post("/api/attendance/uc/token", payload, headers=headers)
        token_data = data.get("data") or {}
        attendance_token = token_data.get("token")
        expire = token_data.get("expire")
        if not attendance_token:
            raise AttendanceClientError("换取考勤 token 成功但未返回 token")
        return AttendanceTokens(main_token=main_token, attendance_token=attendance_token, attendance_token_expire=expire)

    def fetch_records_page(
        self,
        attendance_token: str,
        source_org_id: str,
        attendance_org_id: str,
        member_id: str,
        start_time_ms: int,
        end_time_ms: int,
        page: int = 1,
        size: int = 100,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        第三步：拉取考勤 record/search 单页
        返回：(rows, total)
        """
        headers = {"Authorization": attendance_token}
        payload = {
            "source_org_id": source_org_id,
            "attendance_org_id": attendance_org_id,
            "member_id": member_id,
            "start_time": start_time_ms,
            "end_time": end_time_ms,
            "keyword": "",
            "dept_id": None,
            "page": page,
            "size": size,
        }
        data = self._post("/api/attendance/integration/record/search", payload, headers=headers)
        d = data.get("data") or {}
        rows = d.get("rows") or []
        total = int(d.get("total") or 0)
        if not isinstance(rows, list):
            raise AttendanceClientError("record/search 返回 rows 非列表")
        return rows, total

    def fetch_records_all(
        self,
        attendance_token: str,
        source_org_id: str,
        attendance_org_id: str,
        member_id: str,
        start_time_ms: int,
        end_time_ms: int,
        size: int = 100,
        max_pages: int = 2000,
    ) -> List[Dict[str, Any]]:
        """
        拉取指定时间范围内所有 records（自动翻页）
        - max_pages 防止第三方接口异常导致死循环
        """
        all_rows: List[Dict[str, Any]] = []
        page = 1
        total = 0

        while page <= max_pages:
            rows, total = self.fetch_records_page(
                attendance_token=attendance_token,
                source_org_id=source_org_id,
                attendance_org_id=attendance_org_id,
                member_id=member_id,
                start_time_ms=start_time_ms,
                end_time_ms=end_time_ms,
                page=page,
                size=size,
            )
            all_rows.extend(rows)

            # 结束条件：已取完或该页为空
            if not rows:
                break
            if total and len(all_rows) >= total:
                break

            page += 1

        return all_rows
