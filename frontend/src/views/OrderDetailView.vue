<template>
  <div class="page">
    <div class="topbar">
      <router-link to="/order-search" class="topbar-back">← 返回</router-link>
      <div class="topbar-title">订单明细</div>
      <router-link to="/" class="topbar-home">菜单</router-link>
    </div>

    <div class="body">
      <div v-if="error" class="empty">{{ error }}</div>

      <template v-else>
        <div class="card">
          <div class="card-title">基本信息</div>
          <div class="info-grid">
            <div class="info-item"><span class="lbl">客户</span><span class="val">{{ custDisplay }}</span></div>
            <div class="info-item"><span class="lbl">订单号</span><span class="val mono">{{ head.orders_po }}</span></div>
            <div class="info-item"><span class="lbl">下单日期</span><span class="val">{{ head.order_input_date }}</span></div>
            <div class="info-item"><span class="lbl">交期</span><span class="val">{{ head.order_expect_date }}</span></div>
          </div>
        </div>

        <div class="card">
          <div class="card-title">明细行 <span class="badge">{{ details.length }} 条</span></div>
          <div v-if="details.length === 0" class="empty-inline">暂无明细记录</div>

          <div v-for="(d, i) in details" :key="i" class="detail-row">
            <div class="detail-top">
              <span class="detail-code">{{ d.itemcode }}</span>
              <span class="detail-name">{{ d.itemname }}</span>
            </div>
            <div class="detail-grid">
              <div><span class="lbl">货号</span><span>{{ d.huohao }}</span></div>
              <div><span class="lbl">粗度</span><span>{{ d.cudu }}</span></div>
              <div><span class="lbl">颜色</span><span>{{ d.color }}</span></div>
              <div><span class="lbl">数量</span><span class="bold">{{ d.number }}</span></div>
              <div><span class="lbl">单价</span><span class="price">¥{{ d.sale_price }}</span></div>
              <div><span class="lbl">金额</span><span class="price bold">¥{{ d.sale_value }}</span></div>
              <div><span class="lbl">客户款号</span><span>{{ d.cust_kuanhao || '—' }}</span></div>
              <div><span class="lbl">客户PO</span><span>{{ d.cust_po || '—' }}</span></div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import client from '@/api/client'

interface DetailRow {
  itemcode: string; itemname: string; huohao: string; cudu: string; color: string;
  number: number; sale_price: string; sale_value: string; cust_kuanhao: string; cust_po: string;
}

const route = useRoute()
const head = ref<Record<string, any>>({})
const details = ref<DetailRow[]>([])
const error = ref('')

const custDisplay = computed(() => {
  const short = head.value.cust_short || ''
  const name = head.value.cust_name || ''
  return short !== '' ? `${short} - ${name}` : name
})

onMounted(async () => {
  const orderId = Number(route.params.orderId)
  if (!orderId || orderId <= 0) { error.value = '参数错误：缺少 order_id'; return }
  try {
    const { data } = await client.get(`/orders/${orderId}`)
    head.value = data.head
    details.value = data.details
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '未找到该订单'
  }
})
</script>

<style scoped>
.page { min-height: 100vh; background: #f4f6f9; }

.topbar {
  background: #003366; color: #fff; padding: 12px 16px;
  display: flex; justify-content: space-between; align-items: center;
}
.topbar-title { font-size: 16px; font-weight: 600; }
.topbar-back, .topbar-home { color: #ffeb3b; font-size: 13px; text-decoration: none; }

.body { padding: 12px; }

.card {
  background: #fff; border-radius: 10px;
  padding: 14px 16px; margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,.07);
}
.card-title {
  font-size: 14px; font-weight: 600; color: #003366;
  margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
}
.badge {
  background: #e8f0fe; color: #0052cc;
  font-size: 11px; padding: 2px 7px; border-radius: 10px; font-weight: 500;
}

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.info-item { display: flex; flex-direction: column; gap: 2px; }
.lbl { font-size: 11px; color: #999; }
.val { font-size: 14px; color: #222; }
.mono { font-family: monospace; font-size: 13px; }

.detail-row {
  border-top: 1px dashed #eee; padding-top: 12px; margin-top: 12px;
}
.detail-row:first-of-type { border-top: none; padding-top: 0; margin-top: 0; }
.detail-top { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.detail-code {
  background: #e8f0fe; color: #0052cc;
  font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 600;
}
.detail-name { font-size: 13px; color: #333; }
.detail-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 7px 12px; font-size: 13px;
}
.detail-grid > div { display: flex; flex-direction: column; gap: 1px; }
.detail-grid .lbl { font-size: 11px; color: #999; }
.bold { font-weight: 600; }
.price { color: #c0392b; font-weight: 500; }

.empty, .empty-inline { color: #999; font-size: 13px; padding: 10px 0; }
</style>
