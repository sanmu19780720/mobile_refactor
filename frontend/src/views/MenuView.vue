<template>
  <div>
    <div class="header">
      <div class="header-title">菜单<br /><span style="font-size:12px;">47.107.98.96</span></div>
    </div>

    <div class="container">
      <h2>欢迎：{{ auth.showName }}</h2>

      <ul>
        <li><router-link to="/order-search">订单查询</router-link></li>
        <li><router-link to="/quote-order">查价下单</router-link></li>
      </ul>

      <div class="logout">
        <a href="#" @click.prevent="onLogout">退出登录</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function onLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.header {
  background: #f0f0f0; color: #000; padding: 10px;
  display: flex; justify-content: center; align-items: center;
  border-bottom: 1px solid #ddd;
}
.header-title { font-size: 18px; text-align: center; }
.container { padding: 20px; }
h2 { margin-top: 0; }
ul { list-style-type: disc; padding-left: 20px; font-size: 16px; }
ul li { margin-bottom: 10px; }
.logout { margin-top: 20px; font-size: 16px; }
</style>
