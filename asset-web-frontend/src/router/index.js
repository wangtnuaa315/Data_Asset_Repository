/**
 * router/index.js - Vue Router配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import authApi from '../api/auth'
import { ElMessage } from 'element-plus'

// 路由配置
const routes = [
    {
        path: '/',
        redirect: '/emergency'
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/emergency',
        name: 'Emergency',
        component: () => import('../views/Emergency.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/admin',
        component: () => import('../views/admin/AdminLayout.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
        children: [
            {
                path: '',
                name: 'AdminHub',
                component: () => import('../views/admin/AdminHub.vue')
            },
            {
                path: 'emergency',
                name: 'AdminEmergency',
                component: () => import('../views/admin/AdminEmergency.vue')
            },
            {
                path: 'court',
                name: 'AdminCourt',
                component: () => import('../views/admin/AdminHub.vue') // 占位，复用 Hub
            },
            {
                path: 'system',
                name: 'AdminSystem',
                component: () => import('../views/admin/AdminSystem.vue')
            }
        ]
    }
]

// 创建路由实例
const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
    const isLoggedIn = authApi.isLoggedIn()
    const isAdmin = authApi.isAdmin()

    // 需要登录的页面
    if (to.meta.requiresAuth && !isLoggedIn) {
        ElMessage.warning('请先登录')
        return next('/login')
    }

    // 需要管理员权限
    if (to.meta.requiresAdmin && !isAdmin) {
        ElMessage.warning('需要管理员权限，请使用admin账号登录')
        return next('/login')
    }

    // 已登录用户访问登录页，重定向到首页
    if (to.path === '/login' && isLoggedIn) {
        return next('/emergency')
    }

    next()
})

export default router
