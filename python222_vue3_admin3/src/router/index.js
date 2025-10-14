import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const routes = [
  {
    path: '/',
    name: '主页',
    component: () => import('../layout/index.vue'),
    redirect:'/index',
    children:[
      {
        path: '/index',
        name: '首页',
        component: () => import('../views/index/index.vue')
      },
      {
        path: '/sys/user', //要和数据库一致
        name: '用户管理',
        component: () => import('../views/sys/user/index.vue')
      },
      {
        path: '/sys/role',
        name: '角色管理',
        component: () => import('../views/sys/role/index.vue')
      },
      {
        path: '/sys/menu',
        name: '菜单管理',
        component: () => import('../views/sys/menu/index.vue')
      },
      {
        path: '/bsns/department',
        name: '部门管理',
        component: () => import('../views/bsns/Department')
      },
      {
        path: '/bsns/post',
        name: '岗位管理',
        component: () => import('../views/bsns/Post')
      },
      {
        path:'/userCenter',
        name:'个人中心',
        component:()=>import('../views/userCenter/index')
      },
      {
        path: '/bsns/trainingOverview',
        name: '训练时长总览',
        component: () => import('../views/bsns/TrainingOverview.vue')
      },
      {
        path: '/bsns/trainingAdmin',
        name: '训练记录管理',
        component: () => import('../views/bsns/TrainingAdmin.vue')
      }
    ]
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', public: true }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
