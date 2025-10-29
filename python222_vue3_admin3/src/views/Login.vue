<template>
	<div class="login">
		<el-form ref="loginRef" :model="loginForm" :rules="loginRules" class="login-form">
			<h3 class="title">ZSTU_ACM</h3>

			<el-form-item prop="username">
				<el-input
					v-model="loginForm.username"
					type="text"
					size="large"
					auto-complete="off"
					placeholder="账号"
				>
					<template #prefix><svg-icon icon="user" /></template>
				</el-input>
			</el-form-item>

			<el-form-item prop="password">
				<el-input
					v-model="loginForm.password"
					type="password"
					size="large"
					auto-complete="off"
					placeholder="密码"
				>
					<template #prefix><svg-icon icon="password" /></template>
				</el-input>
			</el-form-item>

			<!-- 验证码区域：左边直接输入，中间是小图，右边放大按钮 -->
			<el-form-item prop="captcha_answer">
				<div class="captcha-line-mini">
					<!-- 小输入框：可以直接输验证码 -->
					<el-input
						v-model="loginForm.captcha_answer"
						class="captcha-inline-input"
						placeholder="验证码"
						maxlength="10"
						@keyup.enter="handleLogin"
					/>

					<!-- 小图（点击刷新） -->
					<img
						:src="captchaImg"
						alt="点击刷新验证码"
						class="captcha-mini-img"
						@click="refreshCaptcha"
					/>

					<!-- 右侧文案区域：放大弹窗 + 刷新提示 -->
					<div class="captcha-mini-ops">
						<el-button
							type="text"
							class="captcha-zoom-btn"
							@click="openCaptchaDialog"
						>
							点击放大输入验证码
						</el-button>
						<div class="captcha-tip">点击图片可刷新</div>
					</div>
				</div>
			</el-form-item>


			<!-- 记住密码 -->
			<el-checkbox v-model="loginForm.rememberMe" style="margin:0px 0px 25px 0px;">
				记住密码
			</el-checkbox>

			<!-- 登录按钮 -->
			<el-form-item style="width:100%;">
				<el-button
					size="large"
					type="primary"
					style="width:100%;"
					@click.prevent="handleLogin"
				>
					<span>登 录</span>
				</el-button>
			</el-form-item>

			<!-- 去注册 -->
			<el-form-item style="width:100%; text-align:center; margin-top:10px;">
				<el-button
					size="default"
					type="text"
					@click="goRegister"
				>
					没有账号？立即注册
				</el-button>
			</el-form-item>
		</el-form>

		<!-- 底部版权 -->
		<div class="el-login-footer">
      <span>Copyright © 2013-2025
        <a href="https://zstuacm.cn" target="_blank">ZSTU_ACM集训队吧 </a> 版权所有.
      </span>
		</div>

		<!-- ====== 大图验证码弹窗 ====== -->
		<el-dialog
			v-model="showCaptchaDialog"
			title="验证码校验"
			width="860px"
			:close-on-click-modal="false"
			:show-close="true"
			@opened="focusCaptchaInput"
		>
			<div class="captcha-dialog-body">
				<!-- 放大图 -->
				<img
					:src="captchaImg"
					class="captcha-big-img"
					alt="验证码"
					@click="refreshCaptcha"
				/>

				<div class="captcha-dialog-hint">
					看不清？点图片刷新
				</div>

				<!-- 输入框放在大图下面 -->
				<el-input
					ref="dialogCaptchaInputRef"
					v-model="tmpCaptchaAnswer"
					size="large"
					placeholder="请输入上图中的验证码"
					@keyup.enter="confirmCaptchaInput"
				/>

				<div class="captcha-dialog-btns">
					<el-button @click="refreshCaptcha">换一张</el-button>
					<el-button type="primary" @click="confirmCaptchaInput">确定</el-button>
				</div>
			</div>
		</el-dialog>
	</div>
</template>


<script setup>
import { ref, onMounted, nextTick } from 'vue'
import requestUtil from '@/util/request'
import qs from 'qs'
import { ElMessage } from 'element-plus'
import Cookies from "js-cookie";
import { encrypt, decrypt } from "@/util/jsencrypt";
import router from '@/router'

const loginForm = ref({
	username: '',
	password: '',
	rememberMe: false,
	// 后端需要的
	captcha_answer: '',
	challenge_id: ''
})

// 只是显示/暂存用
const captchaImg = ref('')
const tmpCaptchaAnswer = ref('') // 弹窗里的临时输入

const loginRef = ref(null)
const showCaptchaDialog = ref(false)
const dialogCaptchaInputRef = ref(null)

const loginRules = {
	username: [{ required: true, trigger: "blur", message: "请输入您的账号" }],
	password: [{ required: true, trigger: "blur", message: "请输入您的密码" }],
	// 注意：现在校验captcha_answer的时候不能只靠blur，
	// 我们在handleLogin里也会额外判断
	captcha_answer: [{ required: true, message: "请先完成验证码校验" }]
};

// 请求验证码
const loadCaptcha = async () => {
	try {
		const res = await requestUtil.get("user/captcha/init")
		const data = res.data
		if (data.code === 200) {
			captchaImg.value = data.img // base64 gif
			loginForm.value.challenge_id = data.challenge_id
			// 这里不要立即清除 loginForm.captcha_answer
			// 因为可能用户已经输过了
			// 但新的 challenge_id 对应的是新验证码，所以应该清掉
			loginForm.value.captcha_answer = ''
			tmpCaptchaAnswer.value = ''
		} else {
			ElMessage.error("获取验证码失败")
		}
	} catch (e) {
		console.error("获取验证码出错: ", e)
		ElMessage.error("验证码加载异常")
	}
}

// 刷新验证码
const refreshCaptcha = async () => {
	await loadCaptcha()
	// 弹窗开着的时候刷新，就把焦点重新放回输入框
	if (showCaptchaDialog.value) {
		await nextTick()
		focusCaptchaInput()
	}
}

// 打开弹窗
const openCaptchaDialog = async () => {
	// 如果当前还没拿到验证码（极端情况），先拉
	if (!captchaImg.value) {
		await loadCaptcha()
	}
	tmpCaptchaAnswer.value = loginForm.value.captcha_answer || ''
	showCaptchaDialog.value = true
	await nextTick()
	focusCaptchaInput()
}

// 弹窗打开后聚焦输入框
const focusCaptchaInput = () => {
	if (dialogCaptchaInputRef.value) {
		dialogCaptchaInputRef.value.focus()
	}
}

// 弹窗“确定”
const confirmCaptchaInput = () => {
	if (!tmpCaptchaAnswer.value || tmpCaptchaAnswer.value.trim() === '') {
		ElMessage.warning("请输入验证码")
		return
	}
	loginForm.value.captcha_answer = tmpCaptchaAnswer.value.trim()
	showCaptchaDialog.value = false
	ElMessage.success("验证码已填写")
}

// 登录
const handleLogin = () => {
	loginRef.value.validate(async (valid) => {
		if (!valid) {
			console.log("验证失败")
			return
		}

		// 二次兜底：防止用户没点弹窗就直接点登录
		if (!loginForm.value.captcha_answer) {
			ElMessage.error("请先完成验证码校验")
			openCaptchaDialog()
			return
		}

		try {
			let result = await requestUtil.post("user/login?" + qs.stringify(loginForm.value))
			let data = result.data
			console.log("login resp:", data)

			if (data.code == 200) {
				ElMessage.success(data.info)
				window.sessionStorage.setItem("token", data.token)

				const currentUser = data.user
				currentUser.roles = data.roles
				window.sessionStorage.setItem("currentUser", JSON.stringify(currentUser))
				window.sessionStorage.setItem("menuList", JSON.stringify(data.menuList))

				// 记住密码逻辑
				if (loginForm.value.rememberMe) {
					Cookies.set("username", loginForm.value.username, { expires: 30 });
					Cookies.set("password", encrypt(loginForm.value.password), { expires: 30 });
					Cookies.set("rememberMe", loginForm.value.rememberMe, { expires: 30 });
				} else {
					Cookies.remove("username");
					Cookies.remove("password");
					Cookies.remove("rememberMe");
				}

				router.replace("/")
			} else {
				ElMessage.error(data.info)
				// 不管是验证码错还是密码错，都换一张，防止复用
				refreshCaptcha()
			}
		} catch (e) {
			console.error("登录请求异常:", e)
			ElMessage.error("登录异常")
			refreshCaptcha()
		}
	})
}

// 读取cookie 自动填用户名/密码
function getCookie() {
	const username = Cookies.get("username");
	const password = Cookies.get("password");
	const rememberMe = Cookies.get("rememberMe");
	loginForm.value.username = username === undefined ? loginForm.value.username : username;
	loginForm.value.password = password === undefined ? loginForm.value.password : decrypt(password);
	loginForm.value.rememberMe = rememberMe === undefined ? false : Boolean(rememberMe);
}

// 点击注册
const goRegister = () => {
	router.push('/register')
}

// 初始化
onMounted(async () => {
	getCookie()
	await loadCaptcha()
})
</script>


<!--<style lang="scss" scoped>-->
<!--a {-->
<!--	color: white-->
<!--}-->
<!--.login {-->
<!--	display: flex;-->
<!--	justify-content: center;-->
<!--	align-items: center;-->
<!--	height: 100%;-->
<!--	background-image: url("../assets/images/login-background.jpg");-->
<!--	background-size: cover;-->
<!--}-->
<!--.title {-->
<!--	margin: 0px auto 30px auto;-->
<!--	text-align: center;-->
<!--	color: #707070;-->
<!--}-->

<!--.login-form {-->
<!--	width: 480px;-->

<!--	/* 我们把卡片的“盒子感”拿掉 */-->
<!--	background: transparent;        /* 透明，而不是白色 */-->
<!--	border-radius: 6px;             /* 圆角留着无所谓，看不到背景就无影响 */-->
<!--	box-shadow: none;               /* 避免阴影像一块板子 */-->

<!--	/* 让里面的排版别太紧凑，还是保留内边距 */-->
<!--	padding: 25px 30px 20px 30px;-->

<!--	/* 让标题和文字在透明背景上也能看清 */-->
<!--	color: #ffffff;-->

<!--	.el-input {-->
<!--		height: 40px;-->
<!--		input {-->
<!--			display: inline-block;-->
<!--			height: 40px;-->
<!--		}-->
<!--	}-->

<!--	.input-icon {-->
<!--		height: 39px;-->
<!--		width: 14px;-->
<!--		margin-left: 0px;-->
<!--	}-->
<!--}-->



<!--.el-login-footer {-->
<!--	height: 40px;-->
<!--	line-height: 40px;-->
<!--	position: fixed;-->
<!--	bottom: 0;-->
<!--	width: 100%;-->
<!--	text-align: center;-->
<!--	color: #fff;-->
<!--	font-family: Arial;-->
<!--	font-size: 12px;-->
<!--	letter-spacing: 1px;-->
<!--}-->
<!--/* 验证码小区域：横向排，小图 + 右侧按钮文字 */-->
<!--.captcha-line-mini {-->
<!--	display: flex;-->
<!--	align-items: flex-start;-->
<!--	width: 100%;-->
<!--	justify-content: flex-end; /* 整块靠右 */-->
<!--}-->

<!--/* 小图本体：我们让它维持和你之前差不多的高度（40px），但是稍微加个圆角和边框 */-->
<!--.captcha-mini-img {-->
<!--	width: 160px;      /* 你可以调大/调小 */-->
<!--	height: 40px;-->
<!--	border-radius: 4px;-->
<!--	border: 1px solid #dcdfe6;-->
<!--	cursor: pointer;-->
<!--	flex-shrink: 0;-->
<!--}-->

<!--/* 小图右边区域：竖排两行文字（放大按钮 + “点击图片可刷新”小提示） */-->
<!--.captcha-mini-ops {-->
<!--	display: flex;-->
<!--	flex-direction: column;-->
<!--	margin-left: 10px;-->
<!--	line-height: 1.2;-->
<!--}-->

<!--.captcha-zoom-btn {-->
<!--	padding: 0;-->
<!--	font-size: 12px;-->
<!--}-->

<!--.captcha-tip {-->
<!--	font-size: 12px;-->
<!--	color: #999;-->
<!--	margin-top: 2px;-->
<!--}-->

<!--/* 弹窗里的区域 */-->
<!--.captcha-dialog-body {-->
<!--	display: flex;-->
<!--	flex-direction: column;-->
<!--	align-items: center;-->

<!--}-->

<!--.captcha-big-img {-->
<!--	width: 800px;-->
<!--	height: 320px;-->
<!--	border: 1px solid #dcdfe6;-->
<!--	border-radius: 6px;-->
<!--	margin-bottom: 10px;-->
<!--	cursor: pointer;-->
<!--	image-rendering: pixelated;-->
<!--}-->


<!--.captcha-dialog-hint {-->
<!--	font-size: 12px;-->
<!--	color: #666;-->
<!--	margin-bottom: 12px;-->
<!--}-->

<!--.captcha-dialog-btns {-->
<!--	margin-top: 12px;-->
<!--	width: 100%;-->
<!--	display: flex;-->
<!--	justify-content: flex-end;-->
<!--	gap: 8px;-->
<!--}-->

<!--</style>-->
<style lang="scss" scoped>
/* 整体背景容器 */
.login {
	display: flex;
	justify-content: center;
	align-items: center;
	height: 100%;
	background-image: url("../assets/images/login-background.jpg");
	background-size: cover;
	background-position: center;
}

/* 标题：亮一点，悬浮感 */
.title {
	margin: 0px auto 30px auto;
	text-align: center;
	color: rgba(255,255,255,0.9);
	font-weight: 500;
	letter-spacing: 0.5px;
}

/* 整个表单容器 => 透明，没有白卡片，没有阴影，只是一个垂直布局区 */
.login-form {
	width: 480px;
	background: transparent;
	border-radius: 8px;
	box-shadow: none;
	padding: 25px 30px 20px 30px;

	color: #fff; /* 让常规文字（复选框文字等）在深背景上清晰 */

	/* 控制 Element Plus 的 el-input 成为“线框风 / 半透明玻璃” */
	:deep(.el-input__wrapper) {
		background-color: rgba(0,0,0,0.25);         /* 半透明深色块 */
		backdrop-filter: blur(4px);                 /* 毛玻璃效果 */
		-webkit-backdrop-filter: blur(4px);
		border: 1px solid rgba(255,255,255,0.4);    /* 细白边框 */
		box-shadow: 0 0 8px rgba(0,0,0,0.6);        /* 一点外发光来区分背景 */
		border-radius: 6px;
	}

	/* 输入框里的文字颜色、placeholder颜色 */
	:deep(.el-input__inner) {
		color: #fff;
		/* placeholder 走 CSS变量，Element Plus 用 --el-input-text-color / --el-input-placeholder-color。
		   为了保险，这里用 ::placeholder 强压一层。*/
		&::placeholder {
			color: rgba(255,255,255,0.55);
		}
	}

	/* 左侧 prefix 图标（小人、锁头）也调亮一点 */
	:deep(.el-input__prefix-inner) {
		color: rgba(255,255,255,0.8);
		svg,
		svg path {
			color: rgba(255,255,255,0.8) !important;
			fill: rgba(255,255,255,0.8) !important;
		}
	}

	/* “记住密码”复选框的文字颜色 */
	:deep(.el-checkbox__label) {
		color: rgba(255,255,255,0.9);
		font-size: 14px;
	}

	/* checkbox 边框 & 背景也别太白板风，这里保持清晰一点 */
	:deep(.el-checkbox__inner) {
		background-color: rgba(0,0,0,0.2);
		border: 1px solid rgba(255,255,255,0.6);
	}
	:deep(.el-checkbox.is-checked .el-checkbox__inner) {
		background-color: #409EFF; /* Element Plus 主色蓝 */
		border-color: #409EFF;
	}
	:deep(.el-checkbox.is-checked .el-checkbox__inner::after) {
		border-color: #fff;
	}

	/* 登录按钮：保持亮蓝填充感，作为主行动按钮 */
	:deep(.el-button.el-button--primary) {
		background-color: #409EFF;
		border-color: #409EFF;
		font-weight: 500;
		letter-spacing: 2px;
	}
	:deep(.el-button.el-button--primary:hover) {
		filter: brightness(1.08);
	}

	/* “没有账号？立即注册” 这个文字按钮的颜色（默认是灰，调成蓝） */
	:deep(.el-button.el-button--text) {
		color: #409EFF;
	}
	:deep(.el-button.el-button--text:hover) {
		color: #66b1ff;
	}
}

/* 页脚版权文字颜色保持白 */
.el-login-footer {
	height: 40px;
	line-height: 40px;
	position: fixed;
	bottom: 0;
	width: 100%;
	text-align: center;
	color: #fff;
	font-family: Arial;
	font-size: 12px;
	letter-spacing: 1px;

	a {
		color: #409EFF;
		text-decoration: none;
	}
	a:hover {
		color: #66b1ff;
	}
}

/* ========================= */
/* 验证码小区域（登录页里的那行） */
/* ========================= */

.captcha-line-mini {
	display: flex;
	align-items: flex-start;
	width: 100%;
	justify-content: flex-start;   /* 从 flex-end 改成 flex-start：整排回到左边 */
	margin-top: 10px;
	margin-bottom: 10px;
	column-gap: 10px;              /* 新增：给输入框和图片之间留间隔 */
}


/* 小预览图：我们让它也看起来更像“线框模块”而不是一块卡片 */
.captcha-mini-img {
	width: 160px;
	height: 60px;
	border-radius: 6px;
	border: 1px solid rgba(255,255,255,0.4);
	background-color: rgba(0,0,0,0.25);
	box-shadow: 0 0 8px rgba(0,0,0,0.6);
	object-fit: cover;
	cursor: pointer;
	flex-shrink: 0;
}

/* 右边两行（放大 / 刷新提示） */
.captcha-mini-ops {
	display: flex;
	flex-direction: column;
	margin-left: 10px;
	line-height: 1.2;
}

/* 点击放大输入验证码（这是个 el-button type="text"） */
.captcha-zoom-btn {
	padding: 0;
	font-size: 12px;
	color: #409EFF;
	cursor: pointer;
}
.captcha-zoom-btn:hover {
	color: #66b1ff;
}

/* “点击图片可刷新”小提示 */
.captcha-tip {
	font-size: 12px;
	color: rgba(255,255,255,0.8);
	margin-top: 4px;
	user-select: none;
}

/* ========================= */
/* 放大验证码的弹窗部分       */
/* ========================= */

.captcha-dialog-body {
	display: flex;
	flex-direction: column;
	align-items: center;
}

/* 大图验证码：保持你之前的尺寸，不过也给它加同样的线框视觉 */
.captcha-big-img {
	width: 800px;
	height: 320px;
	border: 1px solid rgba(0,0,0,0.4);
	border-radius: 6px;
	background-color: #000;
	margin-bottom: 10px;
	cursor: pointer;
	image-rendering: pixelated;
	box-shadow: 0 0 10px rgba(0,0,0,0.6);
}

/* 弹窗提示文字：暗背景里偏灰 */
.captcha-dialog-hint {
	font-size: 12px;
	color: #666;
	margin-bottom: 12px;
}

/* 弹窗内 按钮区：靠右 */
.captcha-dialog-btns {
	margin-top: 12px;
	width: 100%;
	display: flex;
	justify-content: flex-end;
	gap: 8px;
}

/* 给弹窗里的输入框也套“线框风 / 半透明玻璃” */
.captcha-dialog-body :deep(.el-input__wrapper) {
	background-color: rgba(0,0,0,0.25);
	backdrop-filter: blur(4px);
	-webkit-backdrop-filter: blur(4px);
	border: 1px solid rgba(0,0,0,0.4);
	box-shadow: 0 0 8px rgba(0,0,0,0.6);
	border-radius: 6px;
}
.captcha-dialog-body :deep(.el-input__inner) {
	color: #fff;
	&::placeholder {
		color: rgba(255,255,255,0.55);
	}
}
/* 左：验证码输入框 —— 独立小框 */
.captcha-inline-input {
	width: 160px;   /* 你可以调，比如140px/180px */
	/* 不再用父 height 去撑一整块了，让它自己有自己的玻璃风样式 */

	:deep(.el-input__wrapper) {
		background-color: rgba(0,0,0,0.25);
		backdrop-filter: blur(4px);
		-webkit-backdrop-filter: blur(4px);
		border: 1px solid rgba(255,255,255,0.4);
		box-shadow: 0 0 8px rgba(0,0,0,0.6);
		border-radius: 6px;

		height: 60px;          /* 让验证码输入框本身比之前矮一点，40px高的常规行高 */
		padding: 0 12px;
	}

	:deep(.el-input__inner) {
		color: #fff;
		height: 40px;
		line-height: 40px;
		font-size: 14px;
		&::placeholder {
			color: rgba(255,255,255,0.55);
		}
	}
}


/* 链接/文本默认颜色修正 */
a {
	color: #fff;
	text-decoration: none;
}
a:hover {
	color: #66b1ff;
}
</style>
