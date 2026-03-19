<template>
	<div class="user-center">
		<!-- 左侧个人信息卡片 -->
		<div class="profile-card">
			<div class="profile-banner"></div>
			<div class="profile-body">
				<div class="avatar-wrap">
					<avatar :user="currentUser"/>
				</div>
				<div class="profile-name">{{ currentUser.username }}</div>
				<div class="profile-role">
					<el-tag size="small" type="success" round>{{ currentUser.roles }}</el-tag>
				</div>
				<ul class="info-list">
					<li>
						<span class="info-icon">📱</span>
						<span class="info-label">手机号码</span>
						<span class="info-value">{{ currentUser.phonenumber || '未填写' }}</span>
					</li>
					<li>
						<span class="info-icon">📧</span>
						<span class="info-label">用户邮箱</span>
						<span class="info-value">{{ currentUser.email || '未填写' }}</span>
					</li>
					<li>
						<span class="info-icon">📅</span>
						<span class="info-label">创建日期</span>
						<span class="info-value">{{ currentUser.login_date }}</span>
					</li>
				</ul>
			</div>
		</div>

		<!-- 右侧设置区域 -->
		<div class="settings-card">
			<div class="settings-tabs">
				<div
					class="tab-item"
					:class="{ active: activeTab === 'userinfo' }"
					@click="activeTab = 'userinfo'"
				>
					<span class="tab-icon">👤</span> 基本资料
				</div>
				<div
					class="tab-item"
					:class="{ active: activeTab === 'resetPwd' }"
					@click="activeTab = 'resetPwd'"
				>
					<span class="tab-icon">🔒</span> 修改密码
				</div>
			</div>
			<div class="settings-body">
				<userInfo v-if="activeTab === 'userinfo'" :user="currentUser"/>
				<resetPwd v-if="activeTab === 'resetPwd'" :user="currentUser"/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from 'vue'
import avatar from './components/avatar.vue'
import resetPwd from './components/resetPwd.vue'
import userInfo from './components/userInfo.vue'

const currentUser = JSON.parse(sessionStorage.getItem("currentUser"))
const activeTab = ref("userinfo")
</script>

<style scoped>
.user-center {
	display: flex;
	gap: 24px;
	padding: 24px;
	background: #f0f2f5;
	min-height: 100%;
	box-sizing: border-box;
	align-items: flex-start;
}

/* 左侧个人信息卡片 */
.profile-card {
	width: 280px;
	flex-shrink: 0;
	background: #fff;
	border-radius: 16px;
	overflow: hidden;
	box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.profile-banner {
	height: 90px;
	background: linear-gradient(135deg, #647eff 0%, #42b883 100%);
}

.profile-body {
	padding: 0 24px 24px;
	text-align: center;
}

.avatar-wrap {
	margin-top: -40px;
	margin-bottom: 12px;
	display: flex;
	justify-content: center;
}

:deep(.avatar) {
	width: 80px;
	height: 80px;
	border-radius: 50%;
	border: 3px solid #fff;
	box-shadow: 0 2px 12px rgba(0,0,0,0.15);
	object-fit: cover;
}

:deep(.avatar-uploader .el-upload) {
	border-radius: 50%;
	border: 3px solid #fff;
	box-shadow: 0 2px 12px rgba(0,0,0,0.15);
	width: 80px;
	height: 80px;
	overflow: hidden;
}

:deep(.el-icon.avatar-uploader-icon) {
	width: 80px;
	height: 80px;
	font-size: 22px;
}

.profile-name {
	font-size: 18px;
	font-weight: 700;
	color: #1a1a2e;
	margin-bottom: 8px;
}

.profile-role {
	margin-bottom: 20px;
}

.info-list {
	list-style: none;
	padding: 0;
	margin: 0;
	text-align: left;
}

.info-list li {
	display: flex;
	align-items: center;
	padding: 10px 0;
	border-bottom: 1px solid #f0f0f0;
	font-size: 13px;
	gap: 8px;
}

.info-list li:last-child {
	border-bottom: none;
}

.info-icon {
	font-size: 16px;
	width: 20px;
	text-align: center;
}

.info-label {
	color: #909399;
	flex-shrink: 0;
}

.info-value {
	color: #303133;
	font-weight: 500;
	margin-left: auto;
	text-align: right;
	word-break: break-all;
}

/* 右侧设置卡片 */
.settings-card {
	flex: 1;
	background: #fff;
	border-radius: 16px;
	overflow: hidden;
	box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.settings-tabs {
	display: flex;
	border-bottom: 1px solid #f0f0f0;
	padding: 0 24px;
}

.tab-item {
	padding: 18px 20px;
	font-size: 14px;
	color: #909399;
	cursor: pointer;
	border-bottom: 2px solid transparent;
	margin-bottom: -1px;
	transition: all 0.2s;
	display: flex;
	align-items: center;
	gap: 6px;
}

.tab-item:hover {
	color: #647eff;
}

.tab-item.active {
	color: #647eff;
	border-bottom-color: #647eff;
	font-weight: 600;
}

.tab-icon {
	font-size: 16px;
}

.settings-body {
	padding: 32px;
}
</style>
