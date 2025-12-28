<template>
	<div class="app-container">
		<el-card>
			<h2>我的请假</h2>

			<!-- 新增请假申请表单 -->
			<el-form :model="createForm" inline label-width="80px" class="create-form">
				<el-form-item label="请假日期">
					<el-date-picker
						v-model="createForm.dateRange"
						type="daterange"
						range-separator="至"
						start-placeholder="开始日期"
						end-placeholder="结束日期"
						value-format="YYYY-MM-DD"
					/>
				</el-form-item>
				<el-form-item label="理由">
					<el-input
						v-model="createForm.reason"
						type="textarea"
						placeholder="可不填"
						style="width: 300px"
						:rows="2"
						clearable
					/>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="submitLeave">提交请假</el-button>
				</el-form-item>
			</el-form>

			<el-divider />

			<!-- 列表部分，按状态切换 -->
			<el-tabs v-model="queryForm.statusTab" @tab-change="handleTabChange">
				<el-tab-pane label="待审批" name="pending" />
				<el-tab-pane label="已通过" name="approved" />
				<el-tab-pane label="已拒绝" name="rejected" />
				<el-tab-pane label="全部" name="all" />
			</el-tabs>

			<el-form inline :model="queryForm" size="default" class="filter-form">
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
				<el-table-column label="操作" width="160">
					<template #default="{ row }">
						<el-button
							v-if="row.status === 'pending'"
							type="danger"
							link
							@click="handleCancel(row)"
						>取消</el-button>
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
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'

const BASE = (typeof process !== 'undefined' && process.env && process.env.VUE_APP_BASE_API)
	? process.env.VUE_APP_BASE_API
	: 'http://localhost:8000'

function authHeader() {
	const t = sessionStorage.getItem('token') || localStorage.getItem('token')
	return t ? { Authorization: t } : {}   // 后端不接受 Bearer 前缀
}

const createForm = ref({
	dateRange: [dayjs().format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')],
	reason: ''
})

const queryForm = ref({
	statusTab: 'pending',
	pageNum: 1,
	pageSize: 10,
	dateRange: []
})

const tableData = ref([])
const total = ref(0)

async function submitLeave() {
	const [from, to] = createForm.value.dateRange || []
	if (!from || !to) {
		alert('请选择请假起止日期')
		return
	}

	const res = await fetch(`${BASE}/bsns/leave/my/add`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json',
			...authHeader()
		},
		body: JSON.stringify({
			from,
			to,
			reason: createForm.value.reason || ''
		}),
		credentials: 'include'
	})
	const json = await res.json()
	if (json.code !== 200) {
		console.error('提交请假失败', json)
		alert(json.msg || '提交请假失败')
		return
	}
	fetchData()
}

async function fetchData() {
	const [from, to] = queryForm.value.dateRange || []
	const status = queryForm.value.statusTab === 'all' ? '' : queryForm.value.statusTab

	const res = await fetch(`${BASE}/bsns/leave/my/list`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json',
			...authHeader()
		},
		body: JSON.stringify({
			pageNum: queryForm.value.pageNum,
			pageSize: queryForm.value.pageSize,
			status,
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

async function handleCancel(row) {
	if (!confirm('确认取消该请假吗？')) {
		return
	}

	const res = await fetch(`${BASE}/bsns/leave/my/cancel`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json',
			...authHeader()
		},
		body: JSON.stringify({ id: row.id }),
		credentials: 'include'
	})
	const json = await res.json()
	if (json.code !== 200) {
		console.error('取消请假失败', json)
		alert(json.msg || '取消请假失败')
		return
	}
	fetchData()
}

function handleTabChange(name) {
	queryForm.value.statusTab = name
	queryForm.value.pageNum = 1
	fetchData()
}

function handlePageChange(page) {
	queryForm.value.pageNum = page
	fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
.app-container { padding: 20px; }
.create-form { margin-bottom: 10px; }
.filter-form { margin: 10px 0; }
</style>
