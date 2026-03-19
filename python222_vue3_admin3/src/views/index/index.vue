<template>
	<div class="dashboard">
		<!-- A. 欢迎横幅 -->
		<div class="welcome-banner">
			<div class="welcome-left">
				<h1 class="welcome-title">{{ greeting }}，{{ username }}</h1>
				<p class="welcome-date">{{ todayStr }}</p>
			</div>
			<div class="welcome-right">
				<el-tag v-for="r in roles" :key="r" type="warning" size="large" effect="dark" style="margin-left:6px">{{ r }}</el-tag>
			</div>
		</div>

		<!-- B. 个人统计卡片 -->
		<el-row :gutter="20" class="stat-row">
			<el-col :xs="12" :sm="12" :md="6">
				<div class="stat-card">
					<div class="stat-accent accent-blue"></div>
					<div class="stat-content">
						<div class="stat-header">
							<span class="stat-label">训练总时长</span>
							<div class="stat-icon-wrap icon-blue">⏱️</div>
						</div>
						<div class="stat-value">{{ formatMinutes(stats.total_minutes) }}</div>
						<div class="stat-footer">近30天累计</div>
					</div>
				</div>
			</el-col>
			<el-col :xs="12" :sm="12" :md="6">
				<div class="stat-card">
					<div class="stat-accent accent-green"></div>
					<div class="stat-content">
						<div class="stat-header">
							<span class="stat-label">训练天数</span>
							<div class="stat-icon-wrap icon-green">📅</div>
						</div>
						<div class="stat-value">{{ stats.total_days }}<span class="stat-unit">天</span></div>
						<div class="stat-footer">近30天累计</div>
					</div>
				</div>
			</el-col>
			<el-col :xs="12" :sm="12" :md="6">
				<div class="stat-card">
					<div class="stat-accent accent-purple"></div>
					<div class="stat-content">
						<div class="stat-header">
							<span class="stat-label">日均训练</span>
							<div class="stat-icon-wrap icon-purple">📊</div>
						</div>
						<div class="stat-value">{{ stats.avg_minutes_per_day }}<span class="stat-unit">分钟</span></div>
						<div class="stat-footer">每日平均时长</div>
					</div>
				</div>
			</el-col>
			<el-col :xs="12" :sm="12" :md="6">
				<div class="stat-card">
					<div class="stat-accent" :class="stats.violationCount > 0 ? 'accent-red' : 'accent-teal'"></div>
					<div class="stat-content">
						<div class="stat-header">
							<span class="stat-label">违规次数</span>
							<div class="stat-icon-wrap" :class="stats.violationCount > 0 ? 'icon-red' : 'icon-teal'">
								{{ stats.violationCount > 0 ? '⚠️' : '✅' }}
							</div>
						</div>
						<div class="stat-value">{{ stats.violationCount }}<span class="stat-unit">次</span></div>
						<div class="stat-footer">{{ stats.violationCount > 0 ? '请注意规范' : '保持良好记录' }}</div>
					</div>
				</div>
			</el-col>
		</el-row>

		<!-- C. 双栏内容区 -->
		<el-row :gutter="16" class="content-row">
			<el-col :xs="24" :sm="24" :md="14">
				<el-card shadow="never" class="section-card">
					<template #header>
						<div class="section-header">
							<span class="section-title">最近7天训练记录</span>
							<el-button type="primary" link @click="navigateTo('/bsns/trainingOverview', '训练时长总览')">查看全部</el-button>
						</div>
					</template>
					<el-skeleton :rows="4" animated :loading="loadingTraining">
						<el-table :data="recentTraining" stripe border size="small">
							<el-table-column prop="date" label="日期" width="120" align="center" />
							<el-table-column label="训练时长" align="center">
								<template #default="{ row }">{{ formatMinutes(row.minutes) }}</template>
							</el-table-column>
							<el-table-column label="达标" width="80" align="center">
								<template #default="{ row }">
									<el-tag :type="row.minutes >= 840 ? 'success' : 'danger'" size="small">
										{{ row.minutes >= 840 ? '达标' : '未达标' }}
									</el-tag>
								</template>
							</el-table-column>
							<el-table-column prop="violation_times" label="违规" width="70" align="center">
								<template #default="{ row }">
									<el-tag v-if="row.violation_times > 0" type="danger" size="small">{{ row.violation_times }}</el-tag>
									<span v-else style="color:#c0c4cc">—</span>
								</template>
							</el-table-column>
						</el-table>
						<el-empty v-if="!loadingTraining && recentTraining.length === 0" description="暂无训练记录" :image-size="60" />
					</el-skeleton>
				</el-card>
			</el-col>
			<el-col :xs="24" :sm="24" :md="10">
				<el-card shadow="never" class="section-card">
					<template #header>
						<div class="section-header">
							<span class="section-title">我的待审批请假</span>
							<el-button type="primary" link @click="navigateTo('/bsns/leaveMy', '我的请假')">查看全部</el-button>
						</div>
					</template>
					<el-skeleton :rows="3" animated :loading="loadingLeave">
						<el-table :data="myPendingLeave" stripe border size="small">
							<el-table-column prop="startDate" label="开始" width="110" align="center" />
							<el-table-column prop="endDate" label="结束" width="110" align="center" />
							<el-table-column prop="reason" label="理由" show-overflow-tooltip />
							<el-table-column prop="createTime" label="申请时间" width="160" />
						</el-table>
						<el-empty v-if="!loadingLeave && myPendingLeave.length === 0" description="暂无待审批请假" :image-size="60" />
					</el-skeleton>
				</el-card>
			</el-col>
		</el-row>

		<!-- D. 快捷导航 -->
		<el-card shadow="never" class="section-card nav-card">
			<template #header><span class="section-title">快捷导航</span></template>
			<div class="nav-grid">
				<div class="nav-item" @click="navigateTo('/bsns/trainingOverview', '训练时长总览')">
					<div class="nav-icon" style="background:linear-gradient(135deg,#647eff,#8b5cf6)">⏱️</div>
					<span>训练时长总览</span>
				</div>
				<div class="nav-item" @click="navigateTo('/bsns/leaveMy', '我的请假')">
					<div class="nav-icon" style="background:linear-gradient(135deg,#42b883,#35495e)">📝</div>
					<span>我的请假</span>
				</div>
				<div class="nav-item" @click="navigateTo('/userCenter', '个人中心')">
					<div class="nav-icon" style="background:linear-gradient(135deg,#a78bfa,#647eff)">👤</div>
					<span>个人中心</span>
				</div>
				<template v-if="isAdmin">
					<div class="nav-item" @click="navigateTo('/bsns/trainingAdmin', '训练记录管理')">
						<div class="nav-icon" style="background:linear-gradient(135deg,#f59e0b,#d97706)">📋</div>
						<span>训练记录管理</span>
					</div>
					<div class="nav-item" @click="navigateTo('/bsns/leaveAdmin', '请假管理')">
						<div class="nav-icon" style="background:linear-gradient(135deg,#f87171,#ef4444)">📑</div>
						<span>请假管理</span>
					</div>
					<div class="nav-item" @click="navigateTo('/bsns/attendanceSyncAdmin', '考勤同步')">
						<div class="nav-icon" style="background:linear-gradient(135deg,#06b6d4,#0891b2)">🔄</div>
						<span>考勤同步</span>
					</div>
				</template>
			</div>
		</el-card>

		<!-- E. 管理员面板 -->
		<template v-if="isAdmin">
			<el-row :gutter="16" class="content-row">
				<el-col :xs="24" :sm="24" :md="12">
					<el-card shadow="never" class="section-card">
						<template #header>
							<div class="section-header">
								<span class="section-title">全局待审批请假</span>
								<el-button type="primary" link @click="navigateTo('/bsns/leaveAdmin', '请假管理')">前往管理</el-button>
							</div>
						</template>
						<el-skeleton :rows="3" animated :loading="loadingAdminLeave">
							<el-table :data="adminPendingLeave" stripe border size="small">
								<el-table-column prop="username" label="用户" width="100" />
								<el-table-column prop="startDate" label="开始" width="110" align="center" />
								<el-table-column prop="endDate" label="结束" width="110" align="center" />
								<el-table-column prop="reason" label="理由" show-overflow-tooltip />
							</el-table>
							<el-empty v-if="!loadingAdminLeave && adminPendingLeave.length === 0" description="暂无待审批请假" :image-size="60" />
						</el-skeleton>
					</el-card>
				</el-col>
				<el-col :xs="24" :sm="24" :md="12">
					<el-card shadow="never" class="section-card">
						<template #header>
							<div class="section-header">
								<span class="section-title">近7天全员训练活动</span>
								<el-button type="primary" link @click="navigateTo('/bsns/trainingAdmin', '训练记录管理')">前往管理</el-button>
							</div>
						</template>
						<el-skeleton :rows="3" animated :loading="loadingAdminTraining">
							<el-table :data="adminRecentTraining" stripe border size="small">
								<el-table-column prop="username" label="用户" width="100" />
								<el-table-column prop="date" label="日期" width="110" align="center" />
								<el-table-column label="时长" align="center">
									<template #default="{ row }">{{ formatMinutes(row.minutes) }}</template>
								</el-table-column>
								<el-table-column label="达标" width="80" align="center">
									<template #default="{ row }">
										<el-tag :type="row.minutes >= 840 ? 'success' : 'danger'" size="small">
											{{ row.minutes >= 840 ? '达标' : '未达标' }}
										</el-tag>
									</template>
								</el-table-column>
							</el-table>
							<el-empty v-if="!loadingAdminTraining && adminRecentTraining.length === 0" description="暂无训练记录" :image-size="60" />
						</el-skeleton>
					</el-card>
				</el-col>
			</el-row>
		</template>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { BASE, authHeader } from '@/util/request'

dayjs.locale('zh-cn')

const store = useStore()
const router = useRouter()

// 用户信息
const currentUser = JSON.parse(sessionStorage.getItem('currentUser') || '{}')
const username = currentUser.username || currentUser.name || '用户'
const roles = Array.isArray(currentUser.roles) ? currentUser.roles : []
const isAdmin = ref(false)

// 时段问候语
const greeting = computed(() => {
	const h = new Date().getHours()
	if (h < 12) return '上午好'
	if (h < 18) return '下午好'
	return '晚上好'
})

const todayStr = dayjs().format('YYYY年MM月DD日 dddd')

// 个人统计
const stats = ref({ total_minutes: 0, total_days: 0, avg_minutes_per_day: 0, violationCount: 0 })
const loadingTraining = ref(false)
const recentTraining = ref([])

// 请假
const loadingLeave = ref(false)
const myPendingLeave = ref([])

// 管理员数据
const loadingAdminLeave = ref(false)
const adminPendingLeave = ref([])
const loadingAdminTraining = ref(false)
const adminRecentTraining = ref([])

// 格式化分钟
function formatMinutes(minutes) {
	if (!minutes) return '0 分钟'
	const h = Math.floor(minutes / 60)
	const m = minutes % 60
	if (h === 0) return `${m} 分钟`
	if (m === 0) return `${h} 小时`
	return `${h}h ${m}m`
}

// 快捷导航：打开标签页并跳转
function navigateTo(path, name) {
	store.commit('ADD_TABS', { path, name })
	router.push(path)
}

// 获取个人训练统计（近30天汇总 + 近7天明细）
async function fetchMyStats() {
	loadingTraining.value = true
	try {
		const from = dayjs().subtract(30, 'day').format('YYYY-MM-DD')
		const to = dayjs().format('YYYY-MM-DD')
		const url = new URL('/bsns/training/my/overview', BASE)
		url.searchParams.set('from', from)
		url.searchParams.set('to', to)
		const res = await fetch(url.toString(), {
			method: 'GET',
			headers: { Accept: 'application/json', ...authHeader() },
			credentials: 'include'
		})
		const json = await res.json()
		const d = (json && json.data) || {}
		stats.value = {
			total_minutes: d.total_minutes ?? 0,
			total_days: d.total_days ?? 0,
			avg_minutes_per_day: d.avg_minutes_per_day ?? 0,
			violationCount: d.violationCount ?? 0
		}
		const byDate = Array.isArray(d.by_date) ? d.by_date : []
		recentTraining.value = byDate.slice(0, 7)
	} catch (e) {
		console.error('获取训练统计失败', e)
	} finally {
		loadingTraining.value = false
	}
}

// 获取我的待审批请假
async function fetchMyLeave() {
	loadingLeave.value = true
	try {
		const res = await fetch(`${BASE}/bsns/leave/my/list`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...authHeader() },
			body: JSON.stringify({ pageNum: 1, pageSize: 5, status: 'pending' }),
			credentials: 'include'
		})
		const json = await res.json()
		const d = (json && json.data) || {}
		myPendingLeave.value = Array.isArray(d.rows) ? d.rows : []
	} catch (e) {
		console.error('获取请假列表失败', e)
	} finally {
		loadingLeave.value = false
	}
}

// 检测管理员并加载管理员数据
async function fetchAdminData() {
	const hasAdminRole = roles.some(r => /admin/i.test(r))
	if (!hasAdminRole) { isAdmin.value = false; return }

	// 尝试调用管理员API，失败则静默隐藏
	try {
		loadingAdminLeave.value = true
		const res = await fetch(`${BASE}/bsns/leave/admin/list`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...authHeader() },
			body: JSON.stringify({ pageNum: 1, pageSize: 5, status: 'pending' }),
			credentials: 'include'
		})
		const json = await res.json()
		if (json.code !== 200) { isAdmin.value = false; return }
		isAdmin.value = true
		const d = (json && json.data) || {}
		adminPendingLeave.value = Array.isArray(d.rows) ? d.rows : []
	} catch { isAdmin.value = false; return }
	finally { loadingAdminLeave.value = false }

	// 管理员训练数据
	loadingAdminTraining.value = true
	try {
		const from = dayjs().subtract(7, 'day').format('YYYY-MM-DD')
		const to = dayjs().format('YYYY-MM-DD')
		const res = await fetch(`${BASE}/bsns/training/admin/search`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...authHeader() },
			body: JSON.stringify({ pageNum: 1, pageSize: 8, from, to }),
			credentials: 'include'
		})
		const json = await res.json()
		if (json.code === 200) {
			const d = (json && json.data) || {}
			adminRecentTraining.value = Array.isArray(d.rows) ? d.rows : []
		}
	} catch (e) { console.error('获取管理员训练数据失败', e) }
	finally { loadingAdminTraining.value = false }
}

onMounted(() => {
	fetchMyStats()
	fetchMyLeave()
	fetchAdminData()
})
</script>

<style scoped>
.dashboard { padding: 20px; background: #f0f2f5; min-height: 100%; }

/* 欢迎横幅 */
.welcome-banner {
	display: flex; align-items: center; justify-content: space-between;
	padding: 28px 32px; margin-bottom: 20px; border-radius: 12px;
	background: linear-gradient(135deg, #647eff 0%, #42b883 100%);
	color: #fff;
}
.welcome-title { margin: 0; font-size: 26px; font-weight: 700; }
.welcome-date { margin: 6px 0 0; font-size: 14px; opacity: 0.85; }

/* 统计卡片 */
.stat-row { margin-bottom: 20px; }
.stat-card {
	background: #fff;
	border-radius: 12px;
	overflow: hidden;
	position: relative;
	box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);
	transition: transform 0.25s, box-shadow 0.25s;
}
.stat-card:hover {
	transform: translateY(-4px);
	box-shadow: 0 6px 24px rgba(0,0,0,0.1);
}
.stat-accent {
	height: 4px; width: 100%;
}
.accent-blue   { background: linear-gradient(90deg, #647eff, #8b5cf6); }
.accent-green  { background: linear-gradient(90deg, #10b981, #34d399); }
.accent-purple { background: linear-gradient(90deg, #a78bfa, #818cf8); }
.accent-red    { background: linear-gradient(90deg, #f87171, #ef4444); }
.accent-teal   { background: linear-gradient(90deg, #14b8a6, #2dd4bf); }
.stat-content { padding: 20px; }
.stat-header {
	display: flex; align-items: center; justify-content: space-between;
	margin-bottom: 12px;
}
.stat-label { font-size: 13px; color: #909399; font-weight: 500; }
.stat-icon-wrap {
	width: 36px; height: 36px; border-radius: 10px;
	display: flex; align-items: center; justify-content: center;
	font-size: 18px;
}
.icon-blue   { background: rgba(100,126,255,0.1); }
.icon-green  { background: rgba(16,185,129,0.1); }
.icon-purple { background: rgba(167,139,250,0.1); }
.icon-red    { background: rgba(248,113,113,0.1); }
.icon-teal   { background: rgba(20,184,166,0.1); }
.stat-value {
	font-size: 32px; font-weight: 800; color: #1a1a2e;
	line-height: 1; letter-spacing: -0.5px;
}
.stat-unit {
	font-size: 14px; font-weight: 500; color: #909399;
	margin-left: 4px;
}
.stat-footer {
	margin-top: 10px; font-size: 12px; color: #c0c4cc;
}

/* 内容区 */
.content-row { margin-bottom: 20px; }
.section-card { border-radius: 12px; border: none; }
.section-header { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 16px; font-weight: 600; color: #303133; }

/* 快捷导航 */
.nav-card { margin-bottom: 20px; }
.nav-grid { display: flex; flex-wrap: wrap; gap: 16px; }
.nav-item {
	display: flex; align-items: center; gap: 12px;
	padding: 14px 20px; border-radius: 10px; cursor: pointer;
	background: #f9fafb; border: 1px solid #e5e7eb;
	transition: all 0.2s;
}
.nav-item:hover { background: #eff6ff; border-color: #647eff; transform: translateY(-2px); }
.nav-icon {
	width: 40px; height: 40px; border-radius: 10px;
	display: flex; align-items: center; justify-content: center;
	font-size: 20px; flex-shrink: 0;
}
.nav-item span { font-size: 14px; font-weight: 500; color: #374151; }

/* 响应式适配 */
@media (max-width: 768px) {
	.dashboard { padding: 12px; }
	.welcome-banner { flex-wrap: wrap; padding: 18px 20px; gap: 8px; }
	.welcome-title { font-size: 20px; }
	.stat-content { padding: 14px; }
	.stat-value { font-size: 24px; }
	.nav-grid { gap: 10px; }
	.nav-item { padding: 10px 14px; flex: 1 1 calc(50% - 10px); min-width: 130px; }
	.section-card { border-radius: 8px; }
}
@media (max-width: 480px) {
	.dashboard { padding: 8px; }
	.welcome-banner { padding: 14px 16px; }
	.welcome-title { font-size: 17px; }
	.welcome-date { font-size: 12px; }
	.stat-value { font-size: 20px; }
	.stat-label { font-size: 12px; }
	.nav-item { flex: 1 1 100%; }
}
</style>
