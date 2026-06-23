<template>
  <div>
    <div class="header">
      <div class="header-title">订单明细：{{ head.order_po }}</div>
      <div class="header-user">
        <router-link to="/order-search">返回查询</router-link>
        <router-link to="/">菜单</router-link>
      </div>
    </div>

    <div class="container">
      <div v-if="error" class="no-data">{{ error }}</div>

      <template v-else>
        <div class="box">
          <div class="line"><span class="label">客户：</span>{{ custDisplay }}</div>
          <div class="line"><span class="label">订单号：</span>{{ head.order_po }}</div>
          <div class="line"><span class="label">下单日期：</span>{{ head.order_input_date }}</div>
          <div class="line"><span class="label">交期：</span>{{ head.order_expect_date }}</div>
        </div>

        <div class="box">
          <div class="line title">明细行</div>

          <div v-if="details.length === 0" class="line">该订单暂无明细记录。</div>

          <div v-for="(d, i) in details" :key="i" class="detail-item">
            <div class="line">
              <span class="tag">{{ d.itemcode }}</span>{{ d.itemname }}
            </div>
            <div class="line">
              <span class="label">货号：</span>{{ d.huohao }}
              &nbsp;&nbsp;<span class="label">粗度：</span>{{ d.cudu }}
            </div>
            <div class="line">
              <span class="label">颜色：</span>{{ d.color }}
              &nbsp;&nbsp;<span class="label">数量：</span>{{ d.number }}
            </div>
            <div class="line">
              <span class="label">单价：</span>{{ d.sale_price }}
              &nbsp;&nbsp;<span class="label">金额：</span>{{ d.sale_value }}
            </div>
            <div class="line">
              <span class="label">客户款号：</span>{{ d.cust_kuanhao }}
              &nbsp;&nbsp;<span class="label">客户PO：</span>{{ d.cust_po }}
            </div>
          </div>
        </div>

        <div class="back-link">
          <router-link to="/order-search">&laquo; 返回订单列表</router-link>
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
  if (!orderId || orderId <= 0) {
    error.value = '参数错误：缺少 order_id'
    return
  }
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
.header { background:#003366; color:#fff; padding:10px; display:flex; justify-content:space-between; align-items:center; }
.header-title { font-size:16px; }
.header-user { font-size:12px; text-align:right; }
.header-user a { color:#ffeb3b !important; margin-left:5px; }
.container { padding:10px; }
.box { background:#fff; border-radius:8px; padding:10px; margin-bottom:10px; border:1px solid #e0e0e0; font-size:13px; }
.line { margin-bottom:4px; color:#555; }
.line.title { font-weight:bold; margin-bottom:8px; }
.line .label { color:#888; }
.detail-item { border-top:1px dashed #eee; padding-top:6px; margin-top:6px; }
.detail-item:first-of-type { border-top:none; padding-top:0; margin-top:0; }
.tag { font-size:11px; padding:1px 4px; border-radius:3px; background:#eee; margin-right:4px; }
.back-link { margin-top:8px; }
.back-link a { font-size:13px; color:#03a9f4; }
.no-data { background:#fff; padding:14px; border-radius:8px; color:#888; }
</style>
