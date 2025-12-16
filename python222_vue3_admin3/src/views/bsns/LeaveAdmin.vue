<template>
	<div class="app-container">
		<el-card>

			<el-form inline :model="queryForm" size="default" class="filter-form">
				<el-form-item label="用户名">
					<el-input v-model="queryForm.username" placeholder="模糊搜索用户名" clearable />
				</el-form-item>
				<el-form-item label="学号">
					<el-input v-model="queryForm.studentNo" placeholder="精确学号" clearable />
				</el-form-item>
				<el-form-item label="状态">
					<el-select v-model="queryForm.status" placeholder="全部" clearable style="width: 140px">
						<el-option label="全部" value="" />
						<el-option label="待审批" value="pending" />
						<el-option label="已通过" value="approved" />
						<el-option label="已拒绝" value="rejected" />
						<el-option label="已取消" value="cancelled" />
					</el-select>
				</el-form-item>
				<el-form-item label="请假日期">
					<el-date-picker
						v-model="queryForm.dateRange"
						type="daterange"
						range-separator="至"
						start-placeholder="开始日期"
						end-placeholder="结束日期"
						value-format="YYYY-MM-DD"
					/>
				</el-form-item>
				<el-button type="primary" @click="fetchData">查询</el-button>
			</el-form>

			<el-table :data="tableData" border stripe>
				<el-table-column prop="username" label="用户名" width="160" />
				<el-table-column prop="student_no" label="学号" width="160" />
				<el-table-column prop="startDate" label="开始日期" width="140" />
				<el-table-column prop="endDate" label="结束日期" width="140" />
				<el-table-column prop="status" label="状态" width="120">
					<template #default="{ row }">
						<el-tag v-if="row.status === 'pending'">待审批</el-tag>
						<el-tag v-else-if="row.status === 'approved'" type="success">已通过</el-tag>
						<el-tag v-else-if="row.status === 'rejected'" type="danger">已拒绝</el-tag>
						<el-tag v-else type="info">已取消</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="reason" label="请假理由" />
				<el-table-column prop="adminComment" label="审批意见" />
				<el-table-column prop="createTime" label="申请时间" width="180" />
				<el-table-column prop="approveTime" label="审批时间" width="180" />
				<el-table-column prop="cancelTime" label="取消时间" width="180" />
				<el-table-column label="操作" width="200" fixed="right">
					<template #default="{ row }">
						<el-button
							v-if="row.status === 'pending'"
							type="success"
							link
							@click="handleApprove(row, 'approve')"
						>同意</el-button>
						<el-button
							v-if="row.status === 'pending'"
							type="danger"
							link
							@click="handleApprove(row, 'reject')"
						>拒绝</el-button>
					</template>
				</el-table-column>
			</el-table>

			<el-pagination
				background
				layout="prev, pager, next, jumper, ->, total"
				:total="total"
				:page-size="queryForm.pageSize"
				:current-page="queryForm.pageNum"
				@current-change="handlePageChange"
				style="margin-top: 20px; text-align: right"
			/>
		</el-card>
	</div>
</template>

<script setup>
import { ref } from 'vue'

const BASE = (typeof process !== 'undefined' && process.env && process.env.VUE_APP_BASE_API)
	? process.env.VUE_APP_BASE_API
	: 'http://localhost:8000'

function authHeader() {
	const t = sessionStorage.getItem('token') || localStorage.getItem('token')
	return t ? { Authorization: t } : {}
}

const queryForm = ref({
	username: '',
	studentNo: '',
	status: 'pending',
	dateRange: [],
	pageNum: 1,
	pageSize: 10
})

const tableData = ref([])
const total = ref(0)

async function fetchData() {
	const [from, to] = queryForm.value.dateRange || []

	const res = await fetch(`${BASE}/bsns/leave/admin/list`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json',
			...authHeader()
		},
		body: JSON.stringify({
			pageNum: queryForm.value.pageNum,
			pageSize: queryForm.value.pageSize,
			username: queryForm.value.username,
			studentNo: queryForm.value.studentNo,
			status: queryForm.value.status,
			from,
			to
		}),
		credentials: 'include'
	})
	const json = await res.json()
	const d = (json && json.data) || { total: 0, rows: [] }
	tableData.value = Array.isArray(d.rows) ? d.rows : []
	total.value = typeof d.total === 'number' ? d.total : 0
}

async function handleApprove(row, action) {
	const comment = window.prompt(
		action === 'approve'
			? '同意该请假？可填写审批意见'
			: '拒绝该请假？可填写审批意见',
		''
	)
	if (comment === null) {
		return
	}

	const res = await fetch(`${BASE}/bsns/leave/admin/approve`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json',
			...authHeader()
		},
		body: JSON.stringify({
			id: row.id,
			action,
			comment
		}),
		credentials: 'include'
	})
	const json = await res.json()
	if (json.code !== 200) {
		console.error('审批失败', json)
		alert(json.msg || '审批失败')
		return
	}
	fetchData()
}

function handlePageChange(page) {
	queryForm.value.pageNum = page
	fetchData()
}

fetchData()
</script>

<style scoped>
.app-container { padding: 20px; }
.filter-form { margin-bottom: 10px; }
</style>
