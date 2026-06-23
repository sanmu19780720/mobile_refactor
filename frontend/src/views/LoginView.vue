<template>
  <div class="login-wrap">
    <h2>登录系统</h2>

    <div v-if="error" class="login-error">{{ error }}</div>

    <form @submit.prevent="onSubmit">
      <div class="row">账号：<input type="text" v-model="username" /></div>
      <div class="row">密码：<input type="password" v-model="password" /></div>
      <button type="submit" :disabled="loading">{{ loading ? '登录中...' : '登录' }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import client from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const router = useRouter()
const auth = useAuthStore()

async function onSubmit() {
  error.value = ''
  // 等价原 login.php：账号或密码为空
  if (username.value.trim() === '' || password.value.trim() === '') {
    error.value = '账号密码不能为空'
    return
  }
  loading.value = true
  try {
    const { data } = await client.post('/auth/login', {
      username: username.value,
      password: password.value,
    })
    auth.setAuth(data)
    router.push({ name: 'menu' })
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '账号或密码错误'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap { padding: 20px; }
h2 { margin-top: 0; }
.login-error { color: red; margin-bottom: 10px; }
.row { margin-bottom: 14px; }
.row input { padding: 6px 8px; border: 1px solid #aaa; border-radius: 4px; font-size: 14px; }
button { padding: 8px 16px; border: none; border-radius: 4px; background: #0052cc; color: #fff; font-size: 14px; }
button:disabled { opacity: 0.6; }
</style>
