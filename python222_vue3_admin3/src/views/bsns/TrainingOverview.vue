<template>
	<div class="app-container">
		<!-- 顶部标题栏 -->
		<div class="page-header">
			<div class="page-title">
				<span class="title-icon">🏋️</span>
				<span>训练时长总览</span>
			</div>
			<div class="filter-bar">
				<el-date-picker
					v-model="dateRange"
					type="daterange"
					range-separator="至"
					start-placeholder="开始日期"
					end-placeholder="结束日期"
					value-format="YYYY-MM-DD"
					style="width:280px"
				/>
				<el-button type="primary" :loading="loading" @click="fetchOverview" style="margin-left:10px">
					查询
				</el-button>
			</div>
		</div>

		<!-- 统计卡片 -->
		<el-row :gutter="16" class="stat-row">
			<el-col :xs="12" :sm="12" :md="6">
				<div class="stat-card stat-blue">
					<div class="stat-icon">⏱️</div>
					<div class="stat-body">
						<div class="stat-value">{{ formatMinutes(overview.total_minutes) }}</div>
						<div class="stat-label">总训练时长</div>
					</div>
				</div>
			</el-col>
			<el-col :xs="12" :sm="12" :md="6">
				<div class="stat-card stat-green">
					<div class="stat-icon">📅</div>
					<div class="stat-body">
						<div class="stat-value">{{ overview.total_days }} <span class="stat-unit">天</span></div>
						<div class="stat-label">总训练天数</div>
					</div>
				</div>
			</el-col>
			<el-col :xs="12" :sm="12" :md="6">
				<div class="stat-card stat-purple">
					<div class="stat-icon">📊</div>
					<div class="stat-body">
						<div class="stat-value">{{ overview.avg_minutes_per_day }} <span class="stat-unit">分钟/天</span></div>
						<div class="stat-label">日均训练时长</div>
					</div>
				</div>
			</el-col>
			<el-col :xs="12" :sm="12" :md="6">
				<div class="stat-card" :class="overview.violationCount > 0 ? 'stat-red' : 'stat-gray'">
					<div class="stat-icon">{{ overview.violationCount > 0 ? '⚠️' : '✅' }}</div>
					<div class="stat-body">
						<div class="stat-value">{{ overview.violationCount }} <span class="stat-unit">次</span></div>
						<div class="stat-label">累计违规次数</div>
					</div>
				</div>
			</el-col>
		</el-row>

		<!-- 明细表格 -->
		<el-card class="table-card" shadow="never">
			<template #header>
				<div class="table-header">
					<span class="table-title">每日训练明细</span>
					<span class="table-count">共 {{ overview.by_date.length }} 条记录</span>
				</div>
			</template>

			<el-table
				:data="overview.by_date"
				stripe
				border
				:row-class-name="rowClassName"
				style="width:100%"
			>
				<el-table-column prop="date" label="日期" width="160" align="center">
					<template #default="{ row }">
						<span :class="isSaturday(row.date) ? 'date-weekend' : ''">
							{{ row.date }}
							<el-tag v-if="isSaturday(row.date)" size="small" type="warning" style="margin-left:4px">周六</el-tag>
						</span>
					</template>
				</el-table-column>

				<el-table-column label="训练时长" min-width="200" align="center">
					<template #default="{ row }">
						<div class="minutes-bar-wrap">
							<div
								class="minutes-bar"
								:style="{ width: barWidth(row.minutes) + '%' }"
								:class="row.minutes >= 840 ? 'bar-ok' : 'bar-warn'"
							></div>
							<span class="minutes-text">{{ formatMinutes(row.minutes) }}</span>
						</div>
					</template>
				</el-table-column>

				<el-table-column label="达标" width="80" align="center">
					<template #default="{ row }">
						<el-tag :type="row.minutes >= 840 ? 'success' : 'danger'" size="small">
							{{ row.minutes >= 840 ? '达标' : '未达标' }}
						</el-tag>
					</template>
				</el-table-column>

				<el-table-column prop="violation_times" label="违规次数" width="100" align="center">
					<template #default="{ row }">
						<el-tag v-if="row.violation_times > 0" type="danger" size="small">{{ row.violation_times }}</el-tag>
						<span v-else class="text-muted">—</span>
					</template>
				</el-table-column>

				<el-table-column prop="violation_reason" label="违规原因" min-width="200" show-overflow-tooltip>
					<template #default="{ row }">
						<span v-if="row.violation_reason" class="violation-reason">{{ row.violation_reason }}</span>
						<span v-else class="text-muted">—</span>
					</template>
				</el-table-column>
			</el-table>

			<el-empty v-if="!loading && overview.by_date.length === 0" description="暂无训练记录" />
		</el-card>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import dayjs from 'dayjs'
import { BASE, authHeader } from '@/util/request'

const dateRange = ref([dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')])
const loading = ref(false)
const overview = ref({ total_minutes: 0, total_days: 0, avg_minutes_per_day: 0, by_date: [], violationCount: 0 })

// 最大分钟数，用于进度条比例计算
const maxMinutes = computed(() => {
	const max = Math.max(...overview.value.by_date.map(r => r.minutes || 0), 840)
	return max
})

// 格式化分钟为 Xh Ym
function formatMinutes(minutes) {
	if (!minutes) return '0 分钟'
	const h = Math.floor(minutes / 60)
	const m = minutes % 60
	if (h === 0) return `${m} 分钟`
	if (m === 0) return `${h} 小时`
	return `${h}h ${m}m`
}

// 进度条宽度百分比
function barWidth(minutes) {
	if (!maxMinutes.value) return 0
	return Math.min((minutes / maxMinutes.value) * 100, 100)
}

// 是否周六
function isSaturday(dateStr) {
	return dayjs(dateStr).day() === 6
}

// 违规行高亮
function rowClassName({ row }) {
	if (row.violation_times > 0) return 'row-violation'
	return ''
}

async function fetchOverview() {
	const [from, to] = dateRange.value || []
	loading.value = true
	try {
		const url = new URL('/bsns/training/my/overview', BASE)
		url.searchParams.set('from', from || '')
		url.searchParams.set('to', to || '')
		const res = await fetch(url.toString(), {
			method: 'GET',
			headers: { Accept: 'application/json', ...authHeader() },
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
	} finally {
		loading.value = false
	}
}

onMounted(fetchOverview)
</script>

<style scoped>
.app-container {
	padding: 20px;
	background: #f0f2f5;
	min-height: 100%;
}

/* 顶部标题栏 */
.page-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 20px;
}

.page-title {
	font-size: 22px;
	font-weight: 700;
	color: #1a1a2e;
	display: flex;
	align-items: center;
	gap: 8px;
}

.title-icon {
	font-size: 26px;
}

.filter-bar {
	display: flex;
	align-items: center;
}

/* 统计卡片 */
.stat-row {
	margin-bottom: 20px;
}

.stat-card {
	border-radius: 12px;
	padding: 20px 24px;
	display: flex;
	align-items: center;
	gap: 16px;
	transition: transform 0.2s, filter 0.2s;
}

.stat-card:hover {
	transform: translateY(-3px);
	filter: brightness(1.08);
}

.stat-icon {
	font-size: 36px;
	line-height: 1;
}

.stat-value {
	font-size: 26px;
	font-weight: 700;
	line-height: 1.2;
}

.stat-unit {
	font-size: 13px;
	font-weight: 400;
	opacity: 0.75;
}

.stat-label {
	font-size: 13px;
	margin-top: 4px;
	opacity: 0.75;
}

.stat-blue  {
	background: linear-gradient(135deg, #647eff 0%, #8b5cf6 100%);
	box-shadow: 0 4px 20px rgba(100, 126, 255, 0.45);
	color: #fff;
}
.stat-green {
	background: linear-gradient(135deg, #42b883 0%, #35495e 100%);
	box-shadow: 0 4px 20px rgba(66, 184, 131, 0.45);
	color: #fff;
}
.stat-purple {
	background: linear-gradient(135deg, #a78bfa 0%, #647eff 100%);
	box-shadow: 0 4px 20px rgba(167, 139, 250, 0.45);
	color: #fff;
}
.stat-red   {
	background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
	box-shadow: 0 4px 20px rgba(248, 113, 113, 0.45);
	color: #fff;
}
.stat-gray  {
	background: linear-gradient(135deg, #42b883 0%, #647eff 100%);
	box-shadow: 0 4px 20px rgba(66, 184, 131, 0.45);
	color: #fff;
}

/* 表格卡片 */
.table-card {
	border-radius: 12px;
	border: none;
}

.table-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.table-title {
	font-size: 16px;
	font-weight: 600;
	color: #303133;
}

.table-count {
	font-size: 13px;
	color: #909399;
}

/* 日期列 */
.date-weekend {
	color: #e6a23c;
	font-weight: 600;
}

/* 进度条 */
.minutes-bar-wrap {
	position: relative;
	height: 22px;
	background: #f0f0f0;
	border-radius: 11px;
	overflow: hidden;
}

.minutes-bar {
	position: absolute;
	left: 0;
	top: 0;
	height: 100%;
	border-radius: 11px;
	transition: width 0.6s ease;
}

.bar-ok   { background: linear-gradient(90deg, #52c41a, #95de64); }
.bar-warn { background: linear-gradient(90deg, #ff7875, #ffa39e); }

.minutes-text {
	position: absolute;
	right: 8px;
	top: 50%;
	transform: translateY(-50%);
	font-size: 12px;
	font-weight: 600;
	color: #333;
	white-space: nowrap;
}

/* 违规原因 */
.violation-reason {
	color: #f56c6c;
	font-size: 13px;
}

.text-muted {
	color: #c0c4cc;
}

/* 违规行高亮 */
:deep(.row-violation) {
	background-color: #fff5f5 !important;
}

:deep(.row-violation:hover > td) {
	background-color: #ffe9e9 !important;
}

/* 响应式适配 */
@media (max-width: 768px) {
	.app-container { padding: 12px; }
	.page-header { flex-wrap: wrap; gap: 10px; }
	.page-title { font-size: 18px; }
	.stat-card { padding: 14px 16px; }
	.stat-value { font-size: 20px; }
	.stat-icon { font-size: 28px; }
}
</style>
