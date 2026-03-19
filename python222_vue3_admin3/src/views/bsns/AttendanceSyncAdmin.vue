<template>
	<div class="app-container">
		<el-card class="mb12">
			<template #header>
				<div class="card-header">
					<span>考勤同步（得力）</span>
					<div>
						<el-button :loading="loadingState" @click="refreshState">刷新状态</el-button>
						<el-button type="primary" :loading="loadingRun" @click="onRunPipeline">
							一键同步（自动回补）
						</el-button>
					</div>
				</div>
			</template>

			<el-row :gutter="12">
				<el-col :xs="24" :sm="12" :md="8">
					<el-statistic title="最近一次成功同步" :value="state.lastSuccessAt || '-'"></el-statistic>
				</el-col>
				<el-col :xs="24" :sm="12" :md="8">
					<el-statistic title="默认回补天数" :value="state.defaultBackfillDays ?? '-'"></el-statistic>
				</el-col>
				<el-col :xs="24" :sm="12" :md="8">
					<el-statistic title="安全缓冲（分钟）" :value="state.safetyBufferMinutes ?? '-'"></el-statistic>
				</el-col>
			</el-row>

			<el-divider />

			<el-alert
				v-if="state.needTrustCode"
				title="未配置 trustCode，请先保存 trustCode 后再同步"
				type="warning"
				show-icon
				class="mb12"
			/>

			<el-alert
				v-if="state.lastError"
				:title="`最近错误：${state.lastError}`"
				type="error"
				show-icon
				class="mb12"
			/>

			<el-form :inline="true" label-width="100px">
				<el-form-item label="trustCode">
					<el-input
						v-model="form.trustCode"
						placeholder="请输入 trustCode"
						show-password
						style="width: 360px"
					/>
				</el-form-item>
				<el-form-item>
					<el-checkbox v-model="form.runPipeline">保存后立即同步</el-checkbox>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" :loading="loadingSave" @click="onSaveTrustCode">保存</el-button>
				</el-form-item>
			</el-form>
		</el-card>

		<el-card>
			<template #header>
				<div class="card-header">
					<span>同步任务</span>
					<el-button :loading="loadingJobs" @click="refreshJobs">刷新任务列表</el-button>
				</div>
			</template>

			<el-table :data="jobs.rows" border>
				<el-table-column prop="jobId" label="Job ID" min-width="220" />
				<el-table-column prop="status" label="状态" width="110">
					<template #default="{ row }">
						<el-tag :type="statusTagType(row.status)">{{ row.status }}</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="rangeStart" label="开始" min-width="170" />
				<el-table-column prop="rangeEnd" label="结束" min-width="170" />
				<el-table-column prop="insertedCount" label="新增明细" width="110" />
				<el-table-column prop="updatedCount" label="更新明细" width="110" />
				<el-table-column prop="errorMessage" label="错误信息" min-width="220" show-overflow-tooltip />
				<el-table-column prop="createTime" label="创建时间" min-width="170" />
				<el-table-column label="操作" width="120" fixed="right">
					<template #default="{ row }">
						<el-button link type="primary" @click="openJobDetail(row.jobId)">详情</el-button>
					</template>
				</el-table-column>
			</el-table>

			<div class="mt12 pager">
				<el-pagination
					background
					layout="total, prev, pager, next, sizes"
					:total="jobs.total"
					:current-page="query.pageNum"
					:page-size="query.pageSize"
					@current-change="onPageChange"
					@size-change="onSizeChange"
				/>
			</div>
		</el-card>

		<el-drawer v-model="drawer.open" title="任务详情" size="40%">
			<el-descriptions :column="1" border v-if="drawer.detail">
				<el-descriptions-item label="Job ID">{{ drawer.detail.jobId }}</el-descriptions-item>
				<el-descriptions-item label="状态">{{ drawer.detail.status }}</el-descriptions-item>
				<el-descriptions-item label="区间开始">{{ drawer.detail.rangeStart }}</el-descriptions-item>
				<el-descriptions-item label="区间结束">{{ drawer.detail.rangeEnd }}</el-descriptions-item>
				<el-descriptions-item label="断点日期">{{ drawer.detail.cursorDay }}</el-descriptions-item>
				<el-descriptions-item label="断点页">{{ drawer.detail.cursorPage }}</el-descriptions-item>
				<el-descriptions-item label="新增明细">{{ drawer.detail.insertedCount }}</el-descriptions-item>
				<el-descriptions-item label="更新明细">{{ drawer.detail.updatedCount }}</el-descriptions-item>
				<el-descriptions-item label="错误码">{{ drawer.detail.errorCode }}</el-descriptions-item>
				<el-descriptions-item label="错误信息">{{ drawer.detail.errorMessage }}</el-descriptions-item>
				<el-descriptions-item label="开始时间">{{ drawer.detail.startedAt }}</el-descriptions-item>
				<el-descriptions-item label="结束时间">{{ drawer.detail.finishedAt }}</el-descriptions-item>
				<el-descriptions-item label="创建时间">{{ drawer.detail.createTime }}</el-descriptions-item>
				<el-descriptions-item label="更新时间">{{ drawer.detail.updateTime }}</el-descriptions-item>
			</el-descriptions>
		</el-drawer>
	</div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
	apiGetPipelineState,
	apiSaveTrustCode,
	apiRunPipeline,
	apiGetJobs,
	apiGetJobDetail
} from "@/api/attendanceSync";

const loadingState = ref(false);
const loadingSave = ref(false);
const loadingRun = ref(false);
const loadingJobs = ref(false);

const form = reactive({
	trustCode: "",
	runPipeline: true
});

const state = reactive({
	needTrustCode: false,
	lastError: "",
	lastVerifiedAt: "",
	lastSuccessAt: "",
	defaultBackfillDays: 30,
	safetyBufferMinutes: 30,
	lastJob: null
});

const query = reactive({
	pageNum: 1,
	pageSize: 20
});

const jobs = reactive({
	total: 0,
	rows: []
});

const drawer = reactive({
	open: false,
	detail: null
});

function statusTagType(status) {
	if (status === "success") return "success";
	if (status === "failed") return "danger";
	if (status === "running") return "warning";
	return "info";
}

async function refreshState() {
	loadingState.value = true;
	try {
		const resp = await apiGetPipelineState();
		if (resp.code !== 0) {
			ElMessage.error(resp.msg || "获取状态失败");
			return;
		}
		Object.assign(state, resp.data || {});
	} finally {
		loadingState.value = false;
	}
}

async function refreshJobs() {
	loadingJobs.value = true;
	try {
		const resp = await apiGetJobs({ pageNum: query.pageNum, pageSize: query.pageSize });
		if (resp.code !== 0) {
			ElMessage.error(resp.msg || "获取任务列表失败");
			return;
		}
		jobs.total = resp.data?.total || 0;
		jobs.rows = resp.data?.rows || [];
	} finally {
		loadingJobs.value = false;
	}
}

async function onSaveTrustCode() {
	if (!form.trustCode) {
		ElMessage.warning("请输入 trustCode");
		return;
	}
	loadingSave.value = true;
	try {
		const resp = await apiSaveTrustCode({ trustCode: form.trustCode, runPipeline: form.runPipeline });
		if (resp.code !== 0) {
			ElMessage.error(resp.msg || "保存失败");
			return;
		}
		ElMessage.success(resp.msg || "保存成功");
		await refreshState();
		await refreshJobs();
	} finally {
		loadingSave.value = false;
	}
}

async function onRunPipeline() {
	loadingRun.value = true;
	try {
		const resp = await apiRunPipeline();
		if (resp.code !== 0) {
			ElMessage.error(resp.msg || "执行失败");
			return;
		}
		ElMessage.success(resp.msg || "已触发同步");
		await refreshState();
		await refreshJobs();
	} finally {
		loadingRun.value = false;
	}
}

async function openJobDetail(jobId) {
	drawer.open = true;
	drawer.detail = null;
	const resp = await apiGetJobDetail(jobId);
	if (resp.code !== 0) {
		ElMessage.error(resp.msg || "获取详情失败");
		return;
	}
	drawer.detail = resp.data;
}

function onPageChange(p) {
	query.pageNum = p;
	refreshJobs();
}

function onSizeChange(s) {
	query.pageSize = s;
	query.pageNum = 1;
	refreshJobs();
}

onMounted(async () => {
	await refreshState();
	await refreshJobs();
});
</script>

<style scoped>
.mb12 { margin-bottom: 12px; }
.mt12 { margin-top: 12px; }
.pager { display: flex; justify-content: flex-end; }
.card-header { display: flex; align-items: center; justify-content: space-between; }
</style>
