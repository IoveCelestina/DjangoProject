<template>
  <div class="app-wrapper" :class="{ 'mobile': isMobile }">
    <el-container>
      <!-- 移动端遮罩 -->
      <div v-if="isMobile && !collapsed" class="sidebar-overlay" @click="collapsed = true"></div>
      <el-aside :width="collapsed ? '0px' : '200px'" class="sidebar-container"><Menu/></el-aside>
      <div class="collapse-btn" @click="collapsed = !collapsed">
        <el-icon><ArrowLeft v-if="!collapsed"/><ArrowRight v-else/></el-icon>
      </div>
      <el-container>
        <el-header><Header/></el-header>
        <el-main><Tabs/><router-view/></el-main>
        <el-footer><Footer/></el-footer>
      </el-container>
    </el-container>
  </div>
</template>


<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import Menu from '@/layout/menu'
import Header from '@/layout/header'
import Footer from '@/layout/footer'
import Tabs from '@/layout/tabs'

const collapsed = ref(false)
const isMobile = ref(false)

function handleResize() {
  const mobile = window.innerWidth < 768
  isMobile.value = mobile
  if (mobile) collapsed.value = true
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>

.app-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.sidebar-container {
  background-color: #2d3a4b;
  height: 100%;
  overflow: hidden;
  transition: width 0.3s;
  flex-shrink: 0;
}

/* 移动端侧边栏浮动 */
.mobile .sidebar-container {
  position: fixed;
  left: 0; top: 0;
  z-index: 1001;
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 1000;
}

.collapse-btn {
  width: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2d3a4b;
  cursor: pointer;
  color: #fff;
  flex-shrink: 0;
  transition: background-color 0.2s;
  z-index: 10;
}

.collapse-btn:hover {
  background-color: #1f2d3d;
}

.el-container {
  height: 100%
}

.el-header {
  padding-left: 0px;
  padding-right: 0px;
}

:deep(ul.el-menu) {
  border-right-width: 0px
}

@media (max-width: 768px) {
  .collapse-btn { width: 20px; }
  .el-header { height: 50px !important; }
}
</style>
