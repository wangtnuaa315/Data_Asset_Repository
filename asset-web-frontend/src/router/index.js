import { createRouter, createWebHistory } from 'vue-router'
import Emergency from '../views/Emergency.vue'

const routes = [
    {
        path: '/',
        redirect: '/emergency'
    },
    {
        path: '/emergency',
        name: 'Emergency',
        component: Emergency
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
