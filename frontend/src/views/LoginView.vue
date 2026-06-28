<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo">
        <div class="logo-icon">🧵</div>
        <div class="logo-text">线业系统</div>
        <div class="logo-sub">Xianye Management System</div>
      </div>

      <div v-if="error" class="alert-error">{{ error }}</div>

      <form @submit.prevent="onSubmit">
        <div class="field">
          <label>账号</label>
          <input type="text" v-model="username" placeholder="请输入账号" autocomplete="username" />
        </div>
        <div class="field">
          <label>密码</label>
          <input type="password" v-model="password" placeholder="请输入密码" autocomplete="current-password" />
        </div>
        <button type="submit" :disabled="loading" class="btn-login">
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </form>
    </div>
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
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #001f4d 0%, #003380 60%, #0052cc 100%);
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}

.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 36px 28px;
  width: 100%; max-width: 360px;
  box-shadow: 0 8px 32px rgba(0,0,0,.25);
}

.logo { text-align: center; margin-bottom: 28px; }
.logo-icon { font-size: 40px; margin-bottom: 6px; }
.logo-text { font-size: 22px; font-weight: 700; color: #003366; }
.logo-sub { font-size: 11px; color: #aaa; margin-top: 2px; letter-spacing: .5px; }

.alert-error {
  background: #fff2f2; color: #c0392b;
  border: 1px solid #f5c6cb; border-radius: 7px;
  padding: 9px 12px; font-size: 13px; margin-bottom: 16px;
}

.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 500; color: #555; margin-bottom: 6px; }
.field input {
  width: 100%; padding: 11px 13px;
  border: 1px solid #d0d5dd; border-radius: 8px;
  font-size: 14px; box-sizing: border-box;
  outline: none; transition: border-color .2s, box-shadow .2s;
}
.field input:focus {
  border-color: #0052cc;
  box-shadow: 0 0 0 3px rgba(0,82,204,.12);
}

.btn-login {
  width: 100%; padding: 12px;
  background: linear-gradient(90deg, #003366, #0052cc);
  color: #fff; border: none; border-radius: 8px;
  font-size: 16px; font-weight: 600; cursor: pointer;
  margin-top: 6px; transition: opacity .2s;
  letter-spacing: 2px;
}
.btn-login:disabled { opacity: .6; cursor: not-allowed; }
</style>
