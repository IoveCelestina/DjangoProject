<template>
	<div class="app-container">
		<el-card>
			<h2>我的训练时长总览</h2>

			<div class="filter-bar">
				<el-date-picker
					v-model="dateRange"
					type="daterange"
					range-separator="至"
					start-placeholder="开始日期"
					end-placeholder="结束日期"
					value-format="YYYY-MM-DD"
					style="margin-right:10px"
				/>
				<el-button type="primary" @click="fetchOverview">查询</el-button>
			</div>

			<div class="summary">
				<p>总训练时长：<b>{{ overview.total_minutes }}</b> 分钟</p>
				<p>总训练天数：<b>{{ overview.total_days }}</b> 天</p>
				<p>平均每日训练：<b>{{ overview.avg_minutes_per_day }}</b> 分钟</p>
				<p>违规次数: <b>{{overview.violationCount}}</b> 次</p>
			</div>

			<el-divider></el-divider>

			<el-table :data="overview.by_date" stripe>
				<el-table-column prop="date" label="日期" width="200" />
				<el-table-column prop="minutes" label="训练时长（分钟）" />
			</el-table>
		</el-card>
	</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'

const dateRange = ref([dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')])
const overview = ref({ total_minutes: 0, total_days: 0, avg_minutes_per_day: 0, by_date: [],violationCount: 0})

const BASE = (typeof process !== 'undefined' && process.env && process.env.VUE_APP_BASE_API)
	? process.env.VUE_APP_BASE_API
	: 'http://localhost:8000'   // 本地后端兜底

function authHeader() {
	const t = sessionStorage.getItem('token') || localStorage.getItem('token')
	return t ? { Authorization: t } : {}   // 注意：后端不接受 Bearer 前缀
}


async function fetchOverview() {
	const [from, to] = dateRange.value || []
	const url = new URL('/bsns/training/my/overview', BASE)
	url.searchParams.set('from', from || '')
	url.searchParams.set('to', to || '')

	const res = await fetch(url.toString(), {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			...authHeader(),
		},
		credentials: 'include'
	})
	const json = await res.json()
	const d = (json && json.data) || {}
	overview.value = {
		total_minutes: d.total_minutes ?? 0,
		total_days: d.total_days ?? 0,
		avg_minutes_per_day: d.avg_minutes_per_day ?? 0,
		by_date: Array.isArray(d.by_date) ? d.by_date : [],
		violationCount: d.violationCount ?? 0
	}
}





onMounted(fetchOverview)
</script>

<style scoped>
.app-container { padding: 20px; }
.summary p { line-height: 1.8; }
</style>
