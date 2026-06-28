<template>
  <div class="page">
    <div class="topbar">
      <div class="topbar-title">新客户报价</div>
      <router-link to="/" class="topbar-back">← 返回</router-link>
    </div>

    <div class="body">
      <!-- 输入区 -->
      <div class="card">
        <div class="card-title">输入报价信息</div>

        <div class="field">
          <label>货号</label>
          <div class="autocomplete-wrap">
            <input v-model="huohaoKw" placeholder="输入货号关键字搜索" @input="onHuohaoInput" autocomplete="off" />
            <div v-if="huohaoMatches.length" class="dropdown">
              <div v-for="item in huohaoMatches" :key="item.id" class="dropdown-item" @click="selectItem(item)">
                <span class="item-code">{{ item.huohao }}</span>
                <span class="item-name">{{ item.itemname }}</span>
              </div>
            </div>
          </div>
          <div v-if="selectedItem" class="selected-hint">
            已选：{{ selectedItem.huohao }} · {{ selectedItem.length }} · 标准价 ¥{{ selectedItem.price }}
          </div>
        </div>

        <div class="field">
          <label>客户名称</label>
          <input v-model="custName" placeholder="新客户全称" />
        </div>

        <div class="field">
          <label>客户邮箱</label>
          <input v-model="custMail" placeholder="选填" type="email" />
        </div>

        <div class="field">
          <label>折扣</label>
          <div class="discount-row">
            <input v-model.number="discount" placeholder="如 0.85" type="number" min="0.01" max="1" step="0.01" />
            <span v-if="discount > 0 && discount <= 1" class="rate-badge">
              利率 {{ rateDisplay }}
            </span>
          </div>
        </div>

        <div class="btn-row">
          <button class="btn-primary" :disabled="!canGenerate" @click="generate">生成报价单</button>
        </div>
      </div>

      <!-- 报价单 -->
      <div v-if="quoteLines.length" class="card">
        <div class="card-title">报价单 — {{ custName }}</div>
        <div class="quote-meta">折扣：{{ (discount * 100).toFixed(0) }}%&nbsp;&nbsp;利率：{{ rateDisplay }}</div>

        <table class="quote-table">
          <thead>
            <tr><th>货号</th><th>标准长度</th><th>折后价格</th></tr>
          </thead>
          <tbody>
            <tr v-for="(line, i) in quoteLines" :key="i">
              <td>{{ line.huohao }}</td>
              <td>{{ line.length }}</td>
              <td class="price">¥ {{ line.finalPrice }}</td>
            </tr>
          </tbody>
        </table>

        <div class="btn-row">
          <button class="btn-success" :disabled="saving" @click="saveCustomer">
            {{ saving ? '保存中...' : saved ? '✓ 已保存至客户库' : '保存新客户至数据库' }}
          </button>
        </div>
        <div v-if="saveError" class="err">{{ saveError }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import client from '@/api/client'

interface ItemRow { id: number; itemcode: string; itemname: string; huohao: string; cudu: string; length: string; price: number }
interface QuoteLine { huohao: string; length: string; finalPrice: string }

const huohaoKw = ref('')
const huohaoMatches = ref<ItemRow[]>([])
const selectedItem = ref<ItemRow | null>(null)
const custName = ref('')
const custMail = ref('')
const discount = ref<number>(0)
const quoteLines = ref<QuoteLine[]>([])
const saving = ref(false)
const saved = ref(false)
const saveError = ref('')

const rateDisplay = computed(() => {
  if (!discount.value || discount.value <= 0 || discount.value > 1) return ''
  return ((1 - discount.value) * 100).toFixed(1) + '%'
})

const canGenerate = computed(() =>
  selectedItem.value !== null && custName.value.trim() !== '' && discount.value > 0 && discount.value <= 1
)

async function onHuohaoInput() {
  const q = huohaoKw.value.trim()
  if (q.length < 2) { huohaoMatches.value = []; return }
  const { data } = await client.get('/items/by-huohao', { params: { q } })
  huohaoMatches.value = data
}

function selectItem(item: ItemRow) {
  selectedItem.value = item
  huohaoKw.value = item.huohao
  huohaoMatches.value = []
}

function generate() {
  if (!selectedItem.value) return
  saved.value = false
  saveError.value = ''
  const finalPrice = (selectedItem.value.price * discount.value).toFixed(2)
  quoteLines.value = [{
    huohao: selectedItem.value.huohao,
    length: selectedItem.value.length,
    finalPrice,
  }]
}

async function saveCustomer() {
  saving.value = true
  saveError.value = ''
  try {
    await client.post('/customers/new', {
      cust_name: custName.value.trim(),
      cust_mail: custMail.value.trim(),
      cust_discount: discount.value,
    })
    saved.value = true
  } catch (e: any) {
    saveError.value = e?.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #f4f6f9; }

.topbar {
  background: #003366; color: #fff;
  padding: 12px 16px;
  display: flex; justify-content: space-between; align-items: center;
}
.topbar-title { font-size: 17px; font-weight: 600; }
.topbar-back { color: #ffeb3b; font-size: 13px; text-decoration: none; }

.body { padding: 12px; }

.card {
  background: #fff; border-radius: 10px;
  padding: 16px; margin-bottom: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,.07);
}
.card-title { font-size: 15px; font-weight: 600; color: #003366; margin-bottom: 14px; border-bottom: 1px solid #eee; padding-bottom: 8px; }

.field { margin-bottom: 14px; }
.field label { display: block; font-size: 13px; color: #666; margin-bottom: 5px; font-weight: 500; }
.field input {
  width: 100%; padding: 9px 11px; border: 1px solid #d0d5dd;
  border-radius: 7px; font-size: 14px; box-sizing: border-box;
  outline: none; transition: border-color .2s;
}
.field input:focus { border-color: #0052cc; }

.autocomplete-wrap { position: relative; }
.dropdown {
  position: absolute; z-index: 999; width: 100%;
  background: #fff; border: 1px solid #ddd; border-top: none;
  border-radius: 0 0 7px 7px; max-height: 200px; overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0,0,0,.1);
}
.dropdown-item {
  padding: 8px 11px; cursor: pointer; font-size: 13px;
  display: flex; gap: 10px; border-bottom: 1px solid #f5f5f5;
}
.dropdown-item:hover { background: #f0f5ff; }
.item-code { color: #003366; font-weight: 600; min-width: 60px; }
.item-name { color: #666; }

.selected-hint { font-size: 12px; color: #28a745; margin-top: 5px; }

.discount-row { display: flex; align-items: center; gap: 10px; }
.discount-row input { flex: 1; }
.rate-badge {
  background: #fff3cd; color: #856404;
  padding: 5px 10px; border-radius: 20px; font-size: 13px;
  font-weight: 600; white-space: nowrap;
}

.btn-row { text-align: right; margin-top: 16px; }
.btn-primary {
  background: #0052cc; color: #fff;
  padding: 10px 22px; border: none; border-radius: 7px;
  font-size: 14px; cursor: pointer; font-weight: 500;
}
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.btn-success {
  background: #28a745; color: #fff;
  padding: 10px 22px; border: none; border-radius: 7px;
  font-size: 14px; cursor: pointer; font-weight: 500;
}
.btn-success:disabled { opacity: .6; cursor: not-allowed; }

.quote-meta { font-size: 13px; color: #666; margin-bottom: 12px; }
.quote-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.quote-table th {
  background: #f0f5ff; color: #003366;
  padding: 9px 10px; text-align: left; font-weight: 600;
  border-bottom: 2px solid #d0e0ff;
}
.quote-table td { padding: 10px; border-bottom: 1px solid #f0f0f0; }
.quote-table .price { font-weight: 700; color: #c0392b; }

.err { color: #dc3545; font-size: 13px; margin-top: 8px; text-align: right; }
</style>
