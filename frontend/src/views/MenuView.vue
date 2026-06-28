<template>
  <div class="page">
    <div class="topbar">
      <div class="topbar-brand">🧵 线业系统</div>
      <button class="btn-logout" @click="onLogout">退出</button>
    </div>

    <div class="welcome">
      <div class="avatar">{{ initial }}</div>
      <div>
        <div class="welcome-name">{{ auth.showName }}</div>
        <div class="welcome-sub">欢迎回来</div>
      </div>
    </div>

    <div class="menu-grid">
      <router-link to="/order-search" class="menu-card">
        <div class="menu-icon">📋</div>
        <div class="menu-label">订单查询</div>
        <div class="menu-desc">查询客户订单 / 物流信息</div>
      </router-link>

      <router-link to="/quote-order" class="menu-card">
        <div class="menu-icon">💰</div>
        <div class="menu-label">查价下单</div>
        <div class="menu-desc">临时报价 / 批量导入香江</div>
      </router-link>

      <router-link to="/new-customer-quote" class="menu-card">
        <div class="menu-icon">🆕</div>
        <div class="menu-label">新客户报价</div>
        <div class="menu-desc">按货号生成报价单并建档</div>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const initial = computed(() => (auth.showName || '用').charAt(0))

function onLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.page { min-height: 100vh; background: #f4f6f9; }

.topbar {
  background: #003366; color: #fff;
  padding: 12px 16px;
  display: flex; justify-content: space-between; align-items: center;
}
.topbar-brand { font-size: 17px; font-weight: 700; letter-spacing: .5px; }
.btn-logout {
  background: rgba(255,255,255,.15); color: #fff;
  border: 1px solid rgba(255,255,255,.3); border-radius: 6px;
  padding: 5px 12px; font-size: 13px; cursor: pointer;
}

.welcome {
  background: linear-gradient(135deg, #003366, #0052cc);
  color: #fff; padding: 20px 16px;
  display: flex; align-items: center; gap: 14px;
}
.avatar {
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(255,255,255,.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700; flex-shrink: 0;
}
.welcome-name { font-size: 18px; font-weight: 600; }
.welcome-sub { font-size: 12px; opacity: .75; margin-top: 2px; }

.menu-grid {
  padding: 16px; display: flex; flex-direction: column; gap: 12px;
}

.menu-card {
  background: #fff; border-radius: 12px;
  padding: 18px 16px;
  display: flex; align-items: center; gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,.07);
  text-decoration: none; color: inherit;
  transition: box-shadow .2s, transform .1s;
  border: 1px solid #eef0f3;
}
.menu-card:active { transform: scale(.98); box-shadow: 0 2px 8px rgba(0,0,0,.12); }

.menu-icon { font-size: 28px; flex-shrink: 0; }
.menu-label { font-size: 16px; font-weight: 600; color: #003366; }
.menu-desc { font-size: 12px; color: #888; margin-top: 3px; }
</style>
