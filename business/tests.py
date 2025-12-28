from datetime import date, timedelta  # // <--- 新增代码
import json  # // <--- 新增代码
from unittest.mock import patch  # // <--- 新增代码

from django.test import TestCase, RequestFactory  # // <--- 新增代码

from user.models import SysUser  # // <--- 新增代码
from .models import TrainRecord, LeaveRequest  # // <--- 新增代码
from .views_my import (  # // <--- 新增代码
    MyOverviewView,
    MyListView,
    MyLeaveAddView,
    MyLeaveCancelView,
    MyLeaveListView,
)
from .views_admin import (  # // <--- 新增代码
    AdminSearchView,
    LeaveAdminListView,
    LeaveAdminApproveView,
)


class BaseBusinessTestCase(TestCase):  # // <--- 新增代码
    """公共初始化：用户、管理员、RequestFactory"""  # // <--- 新增代码

    def setUp(self):  # // <--- 新增代码
        self.factory = RequestFactory()  # // <--- 新增代码
        # 普通队员用户  # // <--- 新增代码
        self.user = SysUser.objects.create(username="user1", password="pwd123")  # // <--- 新增代码
        # 管理员用户（角色通过 mock get_login_ctx 来决定）  # // <--- 新增代码
        self.admin = SysUser.objects.create(username="admin", password="pwd123")  # // <--- 新增代码

    def json_of(self, response):  # // <--- 新增代码
        """把 JsonResponse 解析成 dict"""  # // <--- 新增代码
        return json.loads(response.content.decode("utf-8"))  # // <--- 新增代码


class TrainingViewsTests(BaseBusinessTestCase):  # // <--- 新增代码
    """训练记录相关视图的测试"""  # // <--- 新增代码

    @patch("business.views_my.get_login_ctx")  # // <--- 新增代码
    def test_my_overview_aggregates_minutes(self, mock_ctx):  # // <--- 新增代码
        """训练总览：返回总分钟数 / 天数 / 日均"""  # // <--- 新增代码
        mock_ctx.return_value = (self.user.id, "member")  # // <--- 新增代码

        # 创建 3 天训练记录：60 + 30 + 90 = 180 分钟  # // <--- 新增代码
        start = date(2025, 1, 1)  # // <--- 新增代码
        minutes_list = [60, 30, 90]  # // <--- 新增代码
        for i, m in enumerate(minutes_list):  # // <--- 新增代码
            TrainRecord.objects.create(  # // <--- 新增代码
                user_id=self.user.id,  # // <--- 新增代码
                date=start + timedelta(days=i),  # // <--- 新增代码
                minutes=m,  # // <--- 新增代码
            )  # // <--- 新增代码

        request = self.factory.get(  # // <--- 新增代码
            "/bsns/training/my/overview",  # // <--- 新增代码
            {"from": "2025-01-01", "to": "2025-01-31"},  # // <--- 新增代码
        )  # // <--- 新增代码

        response = MyOverviewView.as_view()(request)  # // <--- 新增代码
        data = self.json_of(response)  # // <--- 新增代码

        self.assertEqual(data["code"], 200)  # // <--- 新增代码
        self.assertEqual(data["data"]["total_minutes"], sum(minutes_list))  # // <--- 新增代码
        self.assertEqual(data["data"]["total_days"], 3)  # // <--- 新增代码
        self.assertAlmostEqual(  # // <--- 新增代码
            data["data"]["avg_minutes_per_day"],  # // <--- 新增代码
            sum(minutes_list) / 3,  # // <--- 新增代码
            places=1,  # // <--- 新增代码
        )  # // <--- 新增代码
        self.assertEqual(len(data["data"]["by_date"]), 3)  # // <--- 新增代码

    @patch("business.views_my.get_login_ctx")  # // <--- 新增代码
    def test_my_list_filters_by_date_and_user(self, mock_ctx):  # // <--- 新增代码
        """训练列表：只返回当前用户 + 日期范围内的数据"""  # // <--- 新增代码
        mock_ctx.return_value = (self.user.id, "member")  # // <--- 新增代码

        # 当前用户 2 条  # // <--- 新增代码
        TrainRecord.objects.create(  # // <--- 新增代码
            user_id=self.user.id, date=date(2025, 1, 1), minutes=30, source="manual"  # // <--- 新增代码
        )  # // <--- 新增代码
        TrainRecord.objects.create(  # // <--- 新增代码
            user_id=self.user.id, date=date(2025, 1, 2), minutes=40, source="manual"  # // <--- 新增代码
        )  # // <--- 新增代码
        # 其他用户一条，不应出现在列表中  # // <--- 新增代码
        other = SysUser.objects.create(username="other", password="pwd")  # // <--- 新增代码
        TrainRecord.objects.create(  # // <--- 新增代码
            user_id=other.id, date=date(2025, 1, 3), minutes=50, source="manual"  # // <--- 新增代码
        )  # // <--- 新增代码

        payload = {  # // <--- 新增代码
            "pageNum": 1,  # // <--- 新增代码
            "pageSize": 10,  # // <--- 新增代码
            "from": "2025-01-01",  # // <--- 新增代码
            "to": "2025-01-31",  # // <--- 新增代码
            "source": "manual",  # // <--- 新增代码
            "order": "date_desc",  # // <--- 新增代码
        }  # // <--- 新增代码
        request = self.factory.post(  # // <--- 新增代码
            "/bsns/training/my/list",  # // <--- 新增代码
            data=json.dumps(payload),  # // <--- 新增代码
            content_type="application/json",  # // <--- 新增代码
        )  # // <--- 新增代码

        response = MyListView.as_view()(request)  # // <--- 新增代码
        data = self.json_of(response)  # // <--- 新增代码

        self.assertEqual(data["code"], 200)  # // <--- 新增代码
        self.assertEqual(data["data"]["total"], 2)  # // <--- 新增代码
        self.assertEqual(len(data["data"]["rows"]), 2)  # // <--- 新增代码


class LeaveViewsTests(BaseBusinessTestCase):  # // <--- 新增代码
    """请假（队员端）相关视图的测试"""  # // <--- 新增代码

    @patch("business.views_my.get_login_ctx")  # // <--- 新增代码
    def test_my_leave_add_success(self, mock_ctx):  # // <--- 新增代码
        """队员正常提交请假"""  # // <--- 新增代码
        mock_ctx.return_value = (self.user.id, "member")  # // <--- 新增代码

        payload = {  # // <--- 新增代码
            "startDate": "2025-02-01",  # // <--- 新增代码
            "endDate": "2025-02-03",  # // <--- 新增代码
            "reason": "单元测试请假",  # // <--- 新增代码
        }  # // <--- 新增代码
        request = self.factory.post(  # // <--- 新增代码
            "/bsns/leave/my/add",  # // <--- 新增代码
            data=json.dumps(payload),  # // <--- 新增代码
            content_type="application/json",  # // <--- 新增代码
        )  # // <--- 新增代码

        response = MyLeaveAddView.as_view()(request)  # // <--- 新增代码
        data = self.json_of(response)  # // <--- 新增代码

        self.assertEqual(data["code"], 200)  # // <--- 新增代码
        self.assertEqual(LeaveRequest.objects.count(), 1)  # // <--- 新增代码
        leave = LeaveRequest.objects.first()  # // <--- 新增代码
        self.assertEqual(leave.user_id, self.user.id)  # // <--- 新增代码
        self.assertEqual(str(leave.start_date), "2025-02-01")  # // <--- 新增代码
        self.assertEqual(str(leave.end_date), "2025-02-03")  # // <--- 新增代码
        self.assertEqual(leave.status, "pending")  # // <--- 新增代码

    @patch("business.views_my.get_login_ctx")  # // <--- 新增代码
    def test_my_leave_add_missing_date(self, mock_ctx):  # // <--- 新增代码
        """缺少起止日期时返回错误"""  # // <--- 新增代码
        mock_ctx.return_value = (self.user.id, "member")  # // <--- 新增代码

        payload = {"reason": "缺少日期"}  # // <--- 新增代码
        request = self.factory.post(  # // <--- 新增代码
            "/bsns/leave/my/add",  # // <--- 新增代码
            data=json.dumps(payload),  # // <--- 新增代码
            content_type="application/json",  # // <--- 新增代码
        )  # // <--- 新增代码

        response = MyLeaveAddView.as_view()(request)  # // <--- 新增代码
        data = self.json_of(response)  # // <--- 新增代码

        self.assertEqual(data["code"], 400)  # // <--- 新增代码

    @patch("business.views_my.get_login_ctx")  # // <--- 新增代码
    def test_my_leave_cancel_pending_only(self, mock_ctx):  # // <--- 新增代码
        """只有 pending 状态可以取消，取消后变为 cancelled"""  # // <--- 新增代码
        mock_ctx.return_value = (self.user.id, "member")  # // <--- 新增代码

        leave = LeaveRequest.objects.create(  # // <--- 新增代码
            user_id=self.user.id,  # // <--- 新增代码
            start_date=date(2025, 3, 1),  # // <--- 新增代码
            end_date=date(2025, 3, 2),  # // <--- 新增代码
            status="pending",  # // <--- 新增代码
            reason="测试取消",  # // <--- 新增代码
        )  # // <--- 新增代码

        request = self.factory.post(  # // <--- 新增代码
            "/bsns/leave/my/cancel",  # // <--- 新增代码
            data=json.dumps({"id": leave.id}),  # // <--- 新增代码
            content_type="application/json",  # // <--- 新增代码
        )  # // <--- 新增代码

        response = MyLeaveCancelView.as_view()(request)  # // <--- 新增代码
        data = self.json_of(response)  # // <--- 新增代码
        self.assertEqual(data["code"], 200)  # // <--- 新增代码

        leave.refresh_from_db()  # // <--- 新增代码
        self.assertEqual(leave.status, "cancelled")  # // <--- 新增代码
        self.assertIsNotNone(leave.cancel_time)  # // <--- 新增代码

    @patch("business.views_my.get_login_ctx")  # // <--- 新增代码
    def test_my_leave_list_only_self(self, mock_ctx):  # // <--- 新增代码
        """我的请假列表只返回当前用户的记录，并支持按状态过滤"""  # // <--- 新增代码
        mock_ctx.return_value = (self.user.id, "member")  # // <--- 新增代码

        # 当前用户 2 条记录：pending + approved  # // <--- 新增代码
        LeaveRequest.objects.create(  # // <--- 新增代码
            user_id=self.user.id,  # // <--- 新增代码
            start_date=date(2025, 4, 1),  # // <--- 新增代码
            end_date=date(2025, 4, 2),  # // <--- 新增代码
            status="pending",  # // <--- 新增代码
        )  # // <--- 新增代码
        LeaveRequest.objects.create(  # // <--- 新增代码
            user_id=self.user.id,  # // <--- 新增代码
            start_date=date(2025, 5, 1),  # // <--- 新增代码
            end_date=date(2025, 5, 2),  # // <--- 新增代码
            status="approved",  # // <--- 新增代码
        )  # // <--- 新增代码
        # 其他用户一条  # // <--- 新增代码
        other = SysUser.objects.create(username="other2", password="pwd")  # // <--- 新增代码
        LeaveRequest.objects.create(  # // <--- 新增代码
            user_id=other.id,  # // <--- 新增代码
            start_date=date(2025, 4, 1),  # // <--- 新增代码
            end_date=date(2025, 4, 2),  # // <--- 新增代码
            status="pending",  # // <--- 新增代码
        )  # // <--- 新增代码

        payload = {  # // <--- 新增代码
            "pageNum": 1,  # // <--- 新增代码
            "pageSize": 10,  # // <--- 新增代码
            "status": "pending",  # // <--- 新增代码
        }  # // <--- 新增代码
        request = self.factory.post(  # // <--- 新增代码
            "/bsns/leave/my/list",  # // <--- 新增代码
            data=json.dumps(payload),  # // <--- 新增代码
            content_type="application/json",  # // <--- 新增代码
        )  # // <--- 新增代码

        response = MyLeaveListView.as_view()(request)  # // <--- 新增代码
        data = self.json_of(response)  # // <--- 新增代码

        self.assertEqual(data["code"], 200)  # // <--- 新增代码
        self.assertEqual(data["data"]["total"], 1)  # // <--- 新增代码
        self.assertEqual(len(data["data"]["rows"]), 1)  # // <--- 新增代码
        self.assertEqual(data["data"]["rows"][0]["status"], "pending")  # // <--- 新增代码


class AdminViewsTests(BaseBusinessTestCase):  # // <--- 新增代码
    """管理员相关视图的测试（训练 + 请假）"""  # // <--- 新增代码

    @patch("business.views_admin.get_login_ctx")  # // <--- 新增代码
    def test_admin_training_search(self, mock_ctx):  # // <--- 新增代码
        """训练记录管理员查询：能看到指定用户的数据"""  # // <--- 新增代码
        mock_ctx.return_value = (self.admin.id, "admin")  # // <--- 新增代码

        # 为 user 创建训练记录  # // <--- 新增代码
        TrainRecord.objects.create(  # // <--- 新增代码
            user_id=self.user.id, date=date(2025, 6, 1), minutes=100, source="manual"  # // <--- 新增代码
        )  # // <--- 新增代码

        payload = {  # // <--- 新增代码
            "pageNum": 1,  # // <--- 新增代码
            "pageSize": 10,  # // <--- 新增代码
            "userId": self.user.id,  # // <--- 新增代码
            "from": "2025-06-01",  # // <--- 新增代码
            "to": "2025-06-30",  # // <--- 新增代码
        }  # // <--- 新增代码
        request = self.factory.post(  # // <--- 新增代码
            "/bsns/training/admin/search",  # // <--- 新增代码
            data=json.dumps(payload),  # // <--- 新增代码
            content_type="application/json",  # // <--- 新增代码
        )  # // <--- 新增代码

        response = AdminSearchView.as_view()(request)  # // <--- 新增代码
        data = self.json_of(response)  # // <--- 新增代码

        self.assertEqual(data["code"], 200)  # // <--- 新增代码
        self.assertGreaterEqual(data["data"]["total"], 1)  # // <--- 新增代码

    @patch("business.views_admin.get_login_ctx")  # // <--- 新增代码
    def test_admin_leave_list_and_approve(self, mock_ctx):  # // <--- 新增代码
        """管理员可以看到待审批请假并进行审批"""  # // <--- 新增代码
        mock_ctx.return_value = (self.admin.id, "admin")  # // <--- 新增代码

        # 先造一条 pending 请假记录  # // <--- 新增代码
        leave = LeaveRequest.objects.create(  # // <--- 新增代码
            user_id=self.user.id,  # // <--- 新增代码
            start_date=date(2025, 7, 1),  # // <--- 新增代码
            end_date=date(2025, 7, 3),  # // <--- 新增代码
            status="pending",  # // <--- 新增代码
            reason="管理员审批流程测试",  # // <--- 新增代码
        )  # // <--- 新增代码

        # 管理员列表查询  # // <--- 新增代码
        list_payload = {  # // <--- 新增代码
            "pageNum": 1,  # // <--- 新增代码
            "pageSize": 10,  # // <--- 新增代码
            "status": "pending",  # // <--- 新增代码
        }  # // <--- 新增代码
        list_request = self.factory.post(  # // <--- 新增代码
            "/bsns/leave/admin/list",  # // <--- 新增代码
            data=json.dumps(list_payload),  # // <--- 新增代码
            content_type="application/json",  # // <--- 新增代码
        )  # // <--- 新增代码

        list_response = LeaveAdminListView.as_view()(list_request)  # // <--- 新增代码
        list_data = self.json_of(list_response)  # // <--- 新增代码

        self.assertEqual(list_data["code"], 200)  # // <--- 新增代码
        self.assertGreaterEqual(list_data["data"]["total"], 1)  # // <--- 新增代码

        # 管理员审批：同意  # // <--- 新增代码
        approve_payload = {  # // <--- 新增代码
            "id": leave.id,  # // <--- 新增代码
            "action": "approve",  # // <--- 新增代码
            "comment": "同意请假，注意安全",  # // <--- 新增代码
        }  # // <--- 新增代码
        approve_request = self.factory.post(  # // <--- 新增代码
            "/bsns/leave/admin/approve",  # // <--- 新增代码
            data=json.dumps(approve_payload),  # // <--- 新增代码
            content_type="application/json",  # // <--- 新增代码
        )  # // <--- 新增代码

        approve_response = LeaveAdminApproveView.as_view()(approve_request)  # // <--- 新增代码
        approve_data = self.json_of(approve_response)  # // <--- 新增代码

        self.assertEqual(approve_data["code"], 200)  # // <--- 新增代码
        self.assertEqual(approve_data["data"]["status"], "approved")  # // <--- 新增代码

        leave.refresh_from_db()  # // <--- 新增代码
        self.assertEqual(leave.status, "approved")  # // <--- 新增代码
        self.assertEqual(leave.admin_comment, "同意请假，注意安全")  # // <--- 新增代码
        self.assertIsNotNone(leave.decision_time)  # // <--- 新增代码
