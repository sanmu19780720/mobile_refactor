<template>
  <div>
    <div class="header">
      <div class="header-title">订单查询 - 手机系统</div>
      <div class="header-user">
        <span>用户：{{ auth.showName }}</span>
        <router-link to="/quote-order" class="btn-green">查价下单</router-link>
        <router-link to="/order-search" class="btn-blue">订单查询</router-link>
        <a href="#" @click.prevent="onLogout" class="btn-red">退出</a>
      </div>
    </div>

    <div class="container">
      <div class="section-title">查询条件</div>
      <div class="form-box">
        <div class="form-row relative">
          <input type="text" v-model="search.custKeyword" placeholder="输入关键字搜索客户" autocomplete="off"
                 class="full-input" @input="onCustInput" @focus="onCustInput" />
          <div v-if="custMatches.length" class="select-list">
            <div v-for="c in custMatches" :key="c.id" class="select-item" @click="selectCust(c)">
              <template v-if="c.short">{{ c.short }} · {{ c.name }}</template>
              <template v-else>{{ c.name }}</template>
            </div>
          </div>
        </div>

        <div class="form-row">
          <input type="text" v-model="search.keyword" placeholder="可输入客户单号或款号" class="full-input" />
        </div>

        <div class="form-row">
          <label>下单日期范围</label>
          <input type="date" v-model="search.dateFrom" />
          <div class="date-sep">到</div>
          <input type="date" v-model="search.dateTo" />
        </div>

        <div class="btn-row">
          <button type="button" class="btn btn-reset" @click="onReset">重置</button>
          <button type="button" class="btn btn-primary" @click="doSearch">查询</button>
        </div>
      </div>

      <div class="section-title">查询结果（最多显示 50 条）</div>

      <div v-if="loading" class="no-data">查询中...</div>
      <div v-else-if="search.orders.length === 0" class="no-data">没有找到符合条件的订单。</div>

      <div v-for="o in search.orders" :key="o.order_id" class="order-card">
        <div class="order-top">
          <div class="order-po">订单号：{{ o.orders_po }}</div>
          <div class="order-status">
            <span v-if="Number(o.order_status) === 7" class="status-done">全部出货结单</span>
            <span v-else>{{ o.status_text }}</span>
          </div>
        </div>

        <div class="order-line">
          <span class="label">客户：</span>{{ custDisplay(o) }}
          &nbsp;&nbsp;&nbsp;
          <span class="label">总数量：</span>{{ o.total_qty }}
        </div>

        <div class="order-line">
          <span class="label">客户单号：</span>{{ o.cust_po_list }}
          &nbsp;&nbsp;&nbsp;
          <span class="label">客户款号：</span>{{ o.cust_kuanhao_list }}
        </div>

        <div class="order-line">
          <span class="label">下单日期：</span>{{ o.order_input_date }}
          &nbsp;&nbsp;
          <span class="label">交期：</span>{{ o.order_expect_date }}
        </div>

        <div class="order-line">
          <span class="label">出货日期：</span>{{ o.last_chuhuo_date || '—' }}
          &nbsp;&nbsp;
          <span class="label">物流单号：</span>{{ o.wuliu_ids || '—' }}
        </div>

        <div class="order-line">
          <span class="label">收件人：</span>{{ o.recv_man || '—' }}
          &nbsp;&nbsp;
          <span class="label">联系电话：</span>{{ o.recv_call || '—' }}
        </div>

        <div class="order-line">
          <span class="label">客户地址：</span>{{ o.cust_address || '—' }}
        </div>

        <div class="order-actions">
          <a href="#" class="btn-contract" @click.prevent="previewContract(o)">合同预览</a>
          <router-link class="btn-detail" :to="`/order-detail/${o.order_id}`">查看明细</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useOrderSearchStore, type OrderItem } from '@/stores/orderSearch'

interface Customer { id: number; name: string; short: string }

const auth = useAuthStore()
const router = useRouter()
const search = useOrderSearchStore()

const custList = ref<Customer[]>([])
const custMatches = ref<Customer[]>([])
const loading = ref(false)

function custDisplay(o: OrderItem): string {
  if (o.cust_short !== '') return `${o.cust_short} - ${o.cust_name}`
  return o.cust_name
}

function onCustInput() {
  const key = search.custKeyword.trim()
  search.custId = 0
  if (key === '') {
    custMatches.value = []
    return
  }
  const out: Customer[] = []
  for (const c of custList.value) {
    if (c.name.indexOf(key) !== -1 || (c.short && c.short.indexOf(key) !== -1)) {
      out.push(c)
      if (out.length >= 50) break
    }
  }
  custMatches.value = out
}

function selectCust(c: Customer) {
  search.custId = c.id
  search.custKeyword = c.name
  custMatches.value = []
}

async function doSearch() {
  loading.value = true
  try {
    const { data } = await client.get('/orders', {
      params: {
        cust_id: search.custId,
        keyword: search.keyword,
        date_from: search.dateFrom,
        date_to: search.dateTo,
      },
    })
    search.orders = data
  } finally {
    loading.value = false
  }
}

async function previewContract(o: OrderItem) {
  try {
    const resp = await client.get(`/orders/${o.order_id}/contract`, { responseType: 'blob', timeout: 30000 })
    const blob = new Blob([resp.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const win = window.open(url, '_blank')
    // 若被浏览器拦截弹窗，回退为下载
    if (!win) {
      const a = document.createElement('a')
      a.href = url
      a.download = `contract_${o.order_id}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
    }
    // 延迟释放，确保新标签页已加载
    setTimeout(() => window.URL.revokeObjectURL(url), 60000)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    alert(typeof detail === 'string' ? detail : '获取合同预览失败')
  }
}

function onReset() {
  search.reset()
  custMatches.value = []
  doSearch()
}

function onLogout() {
  auth.logout()
  search.reset()
  router.push({ name: 'login' })
}

onMounted(async () => {
  const { data } = await client.get('/customers')
  custList.value = data
  // 已有缓存结果则直接展示，避免返回详情页时清空条件并重查
  if (search.orders.length === 0) {
    doSearch()
  }
})
</script>

<style scoped>
.header { background:#003366; color:#fff; padding:10px; display:flex; justify-content:space-between; align-items:center; }
.header-title { font-size:16px; }
.header-user { font-size:12px; text-align:right; }
.header-user span { margin-right:6px; }
.header-user a { display:inline-block; padding:2px 6px; margin-left:6px; border-radius:3px; color:#fff !important; }
.btn-green { background:#28a745; }
.btn-blue { background:#007bff; }
.btn-red { background:#dc3545; }
.container { padding:10px; }
.section-title { font-weight:bold; margin:10px 0 6px; font-size:15px; }
.form-box { background:#fff; border-radius:8px; padding:10px 12px; border:1px solid #e0e0e0; }
.form-row { margin-bottom:8px; }
.relative { position:relative; }
.full-input { width:100%; padding:6px 8px; border-radius:4px; border:1px solid #aaa; box-sizing:border-box; }
.date-sep { text-align:center; font-size:12px; color:#888; margin:3px 0; }
.select-list { border:1px solid #ddd; border-top:none; max-height:200px; overflow:auto; position:absolute; z-index:999; width:100%; background:#fff; }
.select-item { padding:6px 8px; border-bottom:1px solid #eee; cursor:pointer; font-size:13px; }
.select-item:hover { background:#e8f0fe; }
.btn-row { text-align:right; margin-top:6px; }
.btn { padding:6px 14px; border:none; border-radius:4px; font-size:14px; margin-left:8px; }
.btn-primary { background:#0052cc; color:#fff; }
.btn-reset { background:#ddd; color:#333; }
.no-data { background:#fff; padding:14px; border-radius:8px; color:#888; text-align:center; }
.order-card { background:#fff; border-radius:8px; padding:10px 12px; margin-bottom:10px; border:1px solid #e0e0e0; font-size:13px; }
.order-top { display:flex; justify-content:space-between; margin-bottom:6px; }
.order-po { font-weight:bold; }
.status-done { color:#008000; font-weight:bold; }
.order-line { margin-bottom:4px; color:#555; }
.order-line .label { color:#888; }
.order-actions { margin-top:6px; text-align:right; }
.btn-contract { color:#fff; background:#28a745; font-size:13px; padding:3px 10px; border-radius:3px; margin-right:10px; }
.btn-detail { color:#03a9f4; font-size:13px; }
</style>
