<template>
  <!-- 有用户信息才渲染下拉；没有就显示一个登录入口或什么都不渲染 -->
  <el-dropdown v-if="currentUser">
    <span class="el-dropdown-link">
      <el-avatar shape="square" :size="40" :src="squareUrl">
        <!-- 头像加载失败时显示用户名首字母 -->
        {{ (currentUser.username || '').slice(0, 1).toUpperCase() }}
      </el-avatar>
      &nbsp;&nbsp;{{ currentUser.username }}
      <el-icon class="el-icon--right"><ArrowDown/></el-icon>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item>
			<router-link :to="{ name: '个人中心' }">个人中心</router-link>
		</el-dropdown-item>
        <el-dropdown-item @click="logout">安全退出</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>

  <!-- 没有登录时的兜底（可选） -->
  <span v-else>
    <el-button link type="primary" @click="toLogin">登录</el-button>
  </span>
</template>

<script setup>
import { ArrowDown } from '@element-plus/icons-vue'
import { ref, computed } from 'vue'
import router from '@/router'
import { getServerUrl } from '@/util/request'
import store from '@/store'
function readCurrentUser () {
  try {
    const raw = sessionStorage.getItem('currentUser')
    return raw ? JSON.parse(raw) : null
  } catch (e) {
    console.warn('Invalid currentUser in sessionStorage:', e)
    return null
  }
}

const currentUser = ref(readCurrentUser())

const squareUrl = computed(() => {
  const avatar = currentUser.value?.avatar
  return avatar ? `${getServerUrl()}media/userAvatar/${avatar}` : ''
})

const logout = () => {
  sessionStorage.clear()
  store.commit('RESET_TAB')
  router.replace('/login')
}
const toLogin = () => router.replace('/login')
</script>

<style lang="scss" scoped>
.el-dropdown-link {
  cursor: pointer;
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
}
</style>
