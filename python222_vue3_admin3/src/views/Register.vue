<template>
	<div class="register">
		<el-form :model="form" :rules="rules" ref="formRef" label-width="80px" class="register-form">
			<h3 class="title">注册账号</h3>

			<el-form-item label="用户名" prop="username">
				<el-input v-model="form.username" placeholder="请输入用户名" />
			</el-form-item>

			<el-form-item label="密码" prop="password">
				<el-input type="password" v-model="form.password" placeholder="请输入密码" />
			</el-form-item>

			<el-form-item label="邮箱" prop="email">
				<el-input v-model="form.email" placeholder="请输入邮箱" />
			</el-form-item>

			<el-form-item label="手机号" prop="phonenumber">
				<el-input v-model="form.phonenumber" placeholder="请输入手机号" />
			</el-form-item>

			<el-form-item label="学号" prop="student_no">
				<el-input v-model="form.student_no" placeholder="请输入学号" />
			</el-form-item>

			<el-form-item label="角色" prop="role_id">
				<el-select v-model="form.role_id" placeholder="选择角色">
					<el-option label="正式队员" :value="2" />
					<el-option label="管理员" :value="1" />
				</el-select>
			</el-form-item>

			<el-form-item>
				<el-button type="primary" @click="handleRegister" style="width:100%">注册</el-button>
			</el-form-item>

			<div style="text-align:center">
				<el-button type="text" @click="goLogin">已有账号？返回登录</el-button>
			</div>
		</el-form>
	</div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import requestUtil from '@/util/request'
import router from '@/router'

const form = reactive({
	username: '',
	password: '',
	email: '',
	phonenumber: '',
	student_no: '',
	role_id:'', // 默认正式队员
})

const rules = {
	username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
	password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const formRef = ref()

const handleRegister = async () => {
	formRef.value.validate(async (valid) => {
		if (!valid) return
		try {
			const res = await requestUtil.post('user/register/', form)
			const data = res.data
			if (data.code === 200) {
				ElMessage.success('注册成功，请登录！')
				router.push('/login')
			} else {
				ElMessage.error(data.msg || '注册失败')
			}
		} catch (err) {
			console.error(err)
			ElMessage.error('请求失败，请稍后重试')
		}
	})
}

const goLogin = () => {
	router.push('/login')
}
</script>

<style scoped>
.register {
	display: flex;
	justify-content: center;
	align-items: center;
	height: 100%;
	background: url('../assets/images/login-background.jpg');
	background-size: cover;
}

.register-form {
	background: #fff;
	padding: 30px 30px 10px 30px;
	border-radius: 8px;
	width: 420px;
}

.title {
	text-align: center;
	margin-bottom: 25px;
	color: #606266;
}
</style>
