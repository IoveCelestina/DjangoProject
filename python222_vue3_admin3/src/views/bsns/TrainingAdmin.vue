<template>
	<div class="app-container">
		<el-card>
			<h2>训练记录管理</h2>

			<el-form inline :model="queryForm" size="default" class="filter-form">
				<el-form-item label="用户名">
					<el-input v-model="queryForm.username" placeholder="模糊搜索用户名" clearable />
				</el-form-item>
				<el-form-item label="学号">
					<el-input v-model="queryForm.studentNo" placeholder="精确学号" clearable />
				</el-form-item>
				<el-form-item label="日期范围">
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
				<el-table-column prop="date" label="日期" width="160" />
				<el-table-column prop="minutes" label="训练时长（分钟）" />
				<el-table-column prop="source" label="来源" width="100" />
				<el-table-column prop="violation_times" label="新增违规次数" width="120" />
				<el-table-column prop="violation_reason" label="违规原因" show-overflow-tooltip />
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
import dayjs from 'dayjs'

const BASE = (typeof process !== 'undefined' && process.env && process.env.VUE_APP_BASE_API)
	? process.env.VUE_APP_BASE_API
	: 'http://localhost:8000'

function authHeader() {
	const t = sessionStorage.getItem('token') || localStorage.getItem('token')
	return t ? { Authorization: t } : {}
}


const queryForm = ref({
	pageNum: 1,
	pageSize: 10,
	username: '',
	studentNo: '',
	dateRange: [dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')]
})
const tableData = ref([])
const total = ref(0)


async function fetchData() {
	const [from, to] = queryForm.value.dateRange || []
	const res = await fetch(`${BASE}/bsns/training/admin/search`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json',
			...authHeader(),
		},
		body: JSON.stringify({
			pageNum: queryForm.value.pageNum,
			pageSize: queryForm.value.pageSize,
			username: queryForm.value.username,
			studentNo: queryForm.value.studentNo,
			from, to
		}),
		credentials: 'include'
	})
	const json = await res.json()
	const d = (json && json.data) || { total: 0, rows: [] }
	tableData.value = Array.isArray(d.rows) ? d.rows : []
	total.value = typeof d.total === 'number' ? d.total : 0
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
