import { createRouter, createWebHistory } from 'vue-router'
import Overview from './pages/Overview.vue'
import Windows from './pages/Windows.vue'
import WindowDetail from './pages/WindowDetail.vue'
import Fabrics from './pages/Fabrics.vue'
import Bench from './pages/Bench.vue'
import Fullness from './pages/Fullness.vue'
import History from './pages/History.vue'
import Settings from './pages/Settings.vue'
export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Overview },
    { path: '/windows', component: Windows },
    { path: '/windows/:id', component: WindowDetail, props: true },
    { path: '/fabrics', component: Fabrics },
    { path: '/bench', component: Bench },
    { path: '/fullness', component: Fullness },
    { path: '/history', component: History },
    { path: '/settings', component: Settings },
  ],
})
