<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const WECHAT_OPENID = 'oORbK52yxJyuymhNgGDCpgC4P85o'

onMounted(async () => {
  const isWechat = /MicroMessenger/i.test(navigator.userAgent)
  if (isWechat && !auth.isLoggedIn) {
    try {
      const { data } = await client.post('/auth/wechat', { openid: WECHAT_OPENID })
      auth.setAuth(data)
      router.replace({ name: 'menu' })
    } catch {
      // 非授权用户走正常登录流程
    }
  }
})
</script>
