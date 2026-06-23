import { defineStore } from 'pinia'

interface AuthState {
  token: string
  username: string
  realname: string
  role: string
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: '',
    username: '',
    realname: '',
    role: '',
  }),
  getters: {
    isLoggedIn: (s) => s.token !== '',
    // 等价原 index.php：realname 为空则显示 username
    showName: (s) => (s.realname !== '' ? s.realname : s.username),
  },
  actions: {
    setAuth(payload: { access_token: string; username: string; realname: string; role: string }) {
      this.token = payload.access_token
      this.username = payload.username
      this.realname = payload.realname
      this.role = payload.role
    },
    logout() {
      this.token = ''
      this.username = ''
      this.realname = ''
      this.role = ''
    },
  },
  persist: true,
})
