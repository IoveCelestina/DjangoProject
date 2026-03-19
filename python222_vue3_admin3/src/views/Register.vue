<template>
	<div class="register">
		<el-form ref="formRef" :model="form" :rules="rules" class="register-form">
			<h3 class="title">注册账号</h3>
			<p class="subtitle">ZSTU ACM 集训队管理系统</p>

			<el-form-item prop="username">
				<el-input v-model="form.username" size="large" placeholder="用户名">
					<template #prefix><svg-icon icon="user" /></template>
				</el-input>
			</el-form-item>

			<el-form-item prop="student_no">
				<el-input v-model="form.student_no" size="large" placeholder="学号" />
			</el-form-item>

			<el-form-item prop="password">
				<el-input v-model="form.password" type="password" size="large" placeholder="密码" show-password>
					<template #prefix><svg-icon icon="password" /></template>
				</el-input>
			</el-form-item>

			<el-form-item prop="confirmPwd">
				<el-input v-model="form.confirmPwd" type="password" size="large" placeholder="确认密码" show-password>
					<template #prefix><svg-icon icon="password" /></template>
				</el-input>
			</el-form-item>

			<el-form-item prop="phonenumber">
				<el-input v-model="form.phonenumber" size="large" placeholder="手机号（选填）" />
			</el-form-item>

			<el-form-item prop="email">
				<el-input v-model="form.email" size="large" placeholder="邮箱（选填）" />
			</el-form-item>

			<!-- 角色固定为正式队员 -->
			<div class="role-bar">
				<el-tag type="success" effect="dark" size="large">正式队员</el-tag>
				<span class="role-hint">可查看训练时长、提交请假申请</span>
			</div>

			<el-form-item style="margin-top:20px">
				<el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleRegister">
					注 册
				</el-button>
			</el-form-item>

			<div style="text-align:center">
				<el-button type="text" @click="goLogin">已有账号？返回登录</el-button>
			</div>
		</el-form>

		<div class="register-footer">
			<span>Copyright © 2012-2025&nbsp;&nbsp;<a
				href="https://zstuacm.cn" target="_blank">zstuacm.cn</a>&nbsp;版权所有
			</span>
		</div>
	</div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import requestUtil from '@/util/request'
import router from '@/router'

const formRef = ref()
const loading = ref(false)

const form = reactive({
	username: '',
	password: '',
	confirmPwd: '',
	email: '',
	phonenumber: '',
	student_no: ''
})

// 确认密码校验
const validateConfirmPwd = (rule, value, callback) => {
	if (value !== form.password) {
		callback(new Error('两次输入的密码不一致'))
	} else {
		callback()
	}
}

const rules = {
	username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
	password: [
		{ required: true, message: '请输入密码', trigger: 'blur' },
		{ min: 6, message: '密码至少6位', trigger: 'blur' }
	],
	confirmPwd: [
		{ required: true, message: '请确认密码', trigger: 'blur' },
		{ validator: validateConfirmPwd, trigger: 'blur' }
	],
	student_no: [{ required: true, message: '请输入学号', trigger: 'blur' }]
}

const handleRegister = () => {
	formRef.value.validate(async (valid) => {
		if (!valid) return
		loading.value = true
		try {
			const res = await requestUtil.post('user/register/', {
				username: form.username,
				password: form.password,
				email: form.email,
				phonenumber: form.phonenumber,
				student_no: form.student_no
				// 不传 role_id，后端统一分配"正式队员"
			})
			const data = res.data
			if (data.code === 200) {
				ElMessage.success('注册成功，请登录')
				router.push('/login')
			} else {
				ElMessage.error(data.msg || '注册失败')
			}
		} catch (err) {
			console.error(err)
			ElMessage.error('请求失败，请稍后重试')
		} finally {
			loading.value = false
		}
	})
}

const goLogin = () => { router.push('/login') }
</script>

<style lang="scss" scoped>
.register {
	display: flex;
	justify-content: center;
	align-items: center;
	height: 100%;
	background-image: url("../assets/images/login-background.jpg");
	background-size: cover;
	background-position: center;
}
.title {
	margin: 0 auto 4px auto;
	text-align: center;
	color: rgba(255,255,255,0.9);
	font-weight: 500;
	letter-spacing: 0.5px;
}
.subtitle {
	text-align: center;
	color: rgba(255,255,255,0.55);
	font-size: 13px;
	margin: 0 0 24px 0;
}
.register-form {
	max-width: 460px;
	width: 90%;
	background: transparent;
	border-radius: 8px;
	box-shadow: none;
	padding: 25px 30px 15px 30px;
	color: #fff;

	:deep(.el-input__wrapper) {
		background-color: rgba(0,0,0,0.25);
		backdrop-filter: blur(4px);
		-webkit-backdrop-filter: blur(4px);
		border: 1px solid rgba(255,255,255,0.4);
		box-shadow: 0 0 8px rgba(0,0,0,0.6);
		border-radius: 6px;
	}
	:deep(.el-input__inner) {
		color: #fff;
		&::placeholder { color: rgba(255,255,255,0.55); }
	}
	:deep(.el-input__prefix-inner) {
		color: rgba(255,255,255,0.8);
	}
	:deep(.el-button.el-button--primary) {
		background-color: #409EFF;
		border-color: #409EFF;
		font-weight: 500;
		letter-spacing: 2px;
	}
	:deep(.el-button.el-button--text) {
		color: #409EFF;
	}
	:deep(.el-form-item__error) {
		color: #ff9b9b;
	}
}
.role-bar {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 12px 16px;
	background: rgba(255,255,255,0.08);
	border-radius: 8px;
	border: 1px solid rgba(255,255,255,0.15);
	margin-bottom: 4px;
}
.role-hint {
	font-size: 12px;
	color: rgba(255,255,255,0.6);
}
.register-footer {
	height: 40px;
	line-height: 40px;
	position: fixed;
	bottom: 0;
	width: 100%;
	text-align: center;
	color: #fff;
	font-size: 12px;
	letter-spacing: 1px;
	a { color: #409EFF; text-decoration: none; }
	a:hover { color: #66b1ff; }
}
</style>
