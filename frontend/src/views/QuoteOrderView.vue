<template>
  <div>
    <div class="header-user">
      <span>用户：{{ auth.showName }}</span>
      <router-link to="/quote-order" class="btn-green">查价下单</router-link>
      <router-link to="/order-search" class="btn-blue">订单查询</router-link>
      <a href="#" @click.prevent="onLogout" class="btn-red">退出</a>
    </div>

    <div class="container">
      <div v-if="errorMsg" class="msg-error">{{ errorMsg }}</div>
      <div v-if="infoMsg" class="msg-info">{{ infoMsg }}</div>

      <!-- 一、选择客户 -->
      <div class="section">
        <div class="section-title">客户</div>
        <div class="form-row relative">
          <input type="text" v-model="custKeyword" placeholder="按名称/简称模糊搜索，下拉选择客户"
                 @input="onCustInput" @focus="onCustInput" />
          <div v-if="custMatches.length" class="select-list">
            <div v-for="c in custMatches" :key="c.id" class="select-item" @click="selectCust(c)">
              <template v-if="c.short">{{ c.short }} · {{ c.name }}</template>
              <template v-else>{{ c.name }}</template>
            </div>
          </div>
        </div>
        <div class="hint">已选客户：{{ custName || '未选择' }}</div>
      </div>

      <!-- 二、产品选择 -->
      <div class="section">
        <div class="section-title">产品</div>
        <div class="form-row relative">
          <input type="text" v-model="itemKw" placeholder="输入 2 个以上字符，按 ITEMNAME / ITEMCODE 本地模糊搜索"
                 @input="onItemInput" @focus="onItemInput" />
          <div v-if="itemMatches.length" class="select-list">
            <div v-for="it in itemMatches" :key="it.id" class="select-item" @click="selectItem(it)">
              {{ it.itemname }} [{{ it.itemcode }}]
            </div>
          </div>
        </div>
        <div class="hint">只做本地模糊匹配。选择某个产品后，再显示折扣维护卡片。</div>
      </div>

      <!-- 三、折扣设置（当前产品） -->
      <div v-if="itemDetail" class="section">
        <div class="qo-card">
          <div class="qo-card-title">折扣设置（当前产品）</div>
          <div class="qo-card-sub">
            <strong>{{ itemDetail.itemname }}</strong><br />
            ITEMCODE: {{ itemDetail.itemcode }}
            <template v-if="itemDetail.cudu">&nbsp; 货号/尺寸: {{ itemDetail.cudu }}</template>
          </div>

          <div class="qo-grid qo-grid-2">
            <div class="qo-field">
              <label>产品原价</label>
              <input type="text" :value="itemDetail.price.toFixed(2)" readonly />
              <div class="qo-field-hint">仅显示当前产品原价。</div>
            </div>
            <div class="qo-field">
              <label>客户折扣</label>
              <input type="number" step="0.001" v-model.number="discountForm.discount" />
              <div class="qo-field-hint">例如：-30 表示 7 折；空或 0 表示不打折。</div>
            </div>
            <div class="qo-field">
              <label>客户加价</label>
              <input type="number" step="0.001" v-model.number="discountForm.cust_zhekou_jiajia" />
              <div class="qo-field-hint">在折扣基础上附加的固定加价，空视为 0。</div>
            </div>
            <div class="qo-field">
              <label>佣金比例</label>
              <input type="number" step="0.001" v-model.number="discountForm.cust_yongjin_p" />
              <div class="qo-field-hint">仅内部佣金结算使用，客户不可见，空视为 0。</div>
            </div>
          </div>

          <div class="qo-btn-row">
            <button type="button" class="btn btn-primary" @click="saveDiscount">
              保存 / 更新该客户的折扣设置
            </button>
          </div>
        </div>
      </div>

      <!-- 增加到临时列表 -->
      <div class="qo-card">
        <div class="qo-section-title">增加到临时列表</div>
        <div class="qo-grid qo-grid-2">
          <div class="qo-field">
            <label>客户单号（cust_po）</label>
            <input type="text" v-model="addForm.cust_po" placeholder="手输客户单号" />
          </div>
          <div class="qo-field">
            <label>客户款号（cust_kuanhao）</label>
            <input type="text" v-model="addForm.cust_kuanhao" placeholder="手输客户款号" />
          </div>
          <div class="qo-field">
            <label>颜色</label>
            <input type="text" v-model="addForm.color" placeholder="手输颜色" />
          </div>
          <div class="qo-field">
            <label>数量</label>
            <input type="number" step="1" min="0" v-model.number="addForm.qty" />
            <div class="qo-field-hint qo-field-hint-strong">数量为 0，不会加入临时列表。</div>
          </div>
        </div>
        <div class="qo-btn-row">
          <button type="button" class="btn btn-primary" @click="addToTemp">增加到临时列表</button>
        </div>
      </div>

      <!-- 四、临时报价明细 + 导出 -->
      <div class="section">
        <div class="section-title">临时报价明细</div>
        <div v-if="quote.lines.length === 0" class="hint">
          还没有添加任何行，请先在上面选择产品并加入临时列表。
        </div>
        <template v-else>
          <div class="hint">共 {{ quote.lines.length }} 行。左边客户名仅显示前 8 个汉字。</div>
          <div class="table-wrap">
            <table class="temp-table">
              <thead>
                <tr>
                  <th>流水号</th><th>客户</th><th>客户单号</th><th>客户款号</th><th>ITEMCODE</th>
                  <th>颜色</th><th>数量</th><th>原价</th><th>折扣</th><th>客户加价</th>
                  <th>折后价</th><th>佣金比</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
              <tr v-for="(ln, i) in quote.lines" :key="i">
                <td>{{ serialMap(quote.lines).get(ln.cust_name) }}</td>
                <td>{{ shortCustName(ln.cust_name) }}</td>
                <td>{{ ln.cust_po }}</td>
                <td>{{ ln.cust_kuanhao }}</td>
                <td>{{ ln.itemcode }}</td>
                <td>{{ ln.color }}</td>
                <td>{{ ln.qty }}</td>
                <td>{{ ln.price.toFixed(4) }}</td>
                <td>{{ ln.discount }}</td>
                <td>{{ ln.cust_zhekou_jiajia }}</td>
                <td>{{ finalPrice(ln).toFixed(2) }}</td>
                <td>{{ ln.cust_yongjin_p }}</td>
                <td><span class="icon-del" @click="quote.deleteLine(i)">🗑</span></td>
              </tr>
              </tbody>
            </table>
          </div>

          <div class="qo-card">
            <div class="qo-section-title">高士下单信息（仅高士下单表使用）</div>
            <div class="qo-grid qo-grid-2">
              <div class="qo-field">
                <label>收件地址（Ship to Party）</label>
                <input type="text" v-model="coatsForm.ship_to" placeholder="手动键入收件地址" />
              </div>
              <div class="qo-field">
                <label>买家（Buyer）</label>
                <input type="text" v-model="coatsForm.buyer" placeholder="手动键入买家" />
              </div>
            </div>
            <div class="qo-field-hint">
              客户单号（PO No.）按当月流水号逐行递增自动生成；送货日期 = 今天 + 5 天，自动填入。
            </div>
          </div>

          <div class="bottom-actions">
            <button type="button" class="btn btn-primary" @click="openPreview('batch')">导出批量导入表</button>
            <button type="button" class="btn btn-green2" @click="openPreview('coats')">导出高士下单表</button>
            <button type="button" class="btn btn-danger" @click="clearTemp">清空临时列表</button>
          </div>
        </template>
      </div>

      <!-- 预览弹层 -->
      <div v-if="showPreview" class="preview-overlay">
        <div class="preview-dialog">
          <div class="preview-title">
            导出预览 — 可直接修改表格内容后再导出
            <span class="preview-hint">（修改仅作用于本次导出，不会更新临时列表）</span>
          </div>
          <div class="preview-scroll">
            <table class="preview-table">
              <thead>
                <tr>
                  <th>流水号</th>
                  <th>客户</th>
                  <th>客户单号</th>
                  <th>客户款号</th>
                  <th>ITEMCODE</th>
                  <th>颜色</th>
                  <th>数量</th>
                  <th>原价</th>
                  <th>折扣</th>
                  <th>客户加价</th>
                  <th>折后价</th>
                  <th>佣金比</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(ln, i) in previewLines" :key="i">
                  <td>{{ serialMap(previewLines).get(ln.cust_name) }}</td>
                  <td>{{ shortCustName(ln.cust_name) }}</td>
                  <td><input class="cell-input" v-model="ln.cust_po" /></td>
                  <td><input class="cell-input" v-model="ln.cust_kuanhao" /></td>
                  <td>{{ ln.itemcode }}</td>
                  <td><input class="cell-input" v-model="ln.color" /></td>
                  <td><input class="cell-input cell-num" type="number" step="1" min="0" v-model.number="ln.qty" /></td>
                  <td>{{ ln.price.toFixed(4) }}</td>
                  <td><input class="cell-input cell-num" type="number" step="0.001" v-model.number="ln.discount" /></td>
                  <td><input class="cell-input cell-num" type="number" step="0.001" v-model.number="ln.cust_zhekou_jiajia" /></td>
                  <td>{{ finalPrice(ln).toFixed(2) }}</td>
                  <td><input class="cell-input cell-num" type="number" step="0.001" v-model.number="ln.cust_yongjin_p" /></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="preview-actions">
            <button type="button" class="btn btn-primary" @click="confirmExport">确认导出</button>
            <button v-if="previewTarget === 'batch'" type="button" class="btn btn-import"
              :disabled="importing" @click="importToPc">
              {{ importing ? '导入中…' : '自动导入香江系统' }}
            </button>
            <button type="button" class="btn btn-cancel" @click="showPreview = false">取消</button>
          </div>
          <div v-if="importResult" :class="importResult.ok ? 'msg-info' : 'msg-error'"
               style="margin-top:8px; white-space:pre-line;">
            {{ importResult.msg }}
          </div>
        </div>
      </div>

      <!-- 五、页面说明 -->
      <div class="section">
        <div class="section-title">使用说明（当前页仅用于报价格式）</div>
        <ol class="small-text">
          <li>选择客户；</li>
          <li>按产品 itemname / itemcode 在本地列表中模糊查询，选择产品；</li>
          <li>维护该产品在该客户上的折扣、佣金方式等参数；</li>
          <li>按客户内单号、客户款号、颜色、数量等添加到临时列表；</li>
          <li>提交订单时导出 Excel（以后可对接正式下单流程）。</li>
        </ol>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useQuoteStore, type QuoteLine } from '@/stores/quote'

interface Customer { id: number; name: string; short: string }
interface Item { id: number; itemcode: string; itemname: string; huohao: string; cudu: string; price: number }

const auth = useAuthStore()
const router = useRouter()
const quote = useQuoteStore()

const custList = ref<Customer[]>([])
const itemList = ref<Item[]>([])
const custMatches = ref<Customer[]>([])
const itemMatches = ref<Item[]>([])

const custKeyword = ref('')
const custId = ref(0)
const custName = ref('')

const itemKw = ref('')
const itemId = ref(0)
const itemDetail = ref<Item | null>(null)

const errorMsg = ref('')
const infoMsg = ref('')

const showPreview = ref(false)
const previewTarget = ref<'batch' | 'coats'>('batch')
const previewLines = ref<QuoteLine[]>([])
const nextSeq = ref(1)
const importing = ref(false)
const importResult = ref<{ ok: boolean; msg: string } | null>(null)

const discountForm = reactive({ discount: 0, cust_yongjin_p: 0, cust_zhekou_jiajia: 0 })
const addForm = reactive({ cust_po: '', cust_kuanhao: '', color: '', qty: 0 })
const coatsForm = reactive({ ship_to: '大货地址', buyer: 'XiangJiang 香江' })

// 按客户名分组，同一客户共用同一流水号，从 startSeq 开始递增
function serialMap(lines: QuoteLine[], startSeq: number = nextSeq.value): Map<string, number> {
  const map = new Map<string, number>()
  let seq = startSeq
  for (const ln of lines) {
    if (!map.has(ln.cust_name)) {
      map.set(ln.cust_name, seq++)
    }
  }
  return map
}

// 客户名前 8 个汉字截断，等价 PHP short_cust_name
function shortCustName(name: string): string {
  if (!name) return ''
  const chars = Array.from(name)
  if (chars.length > 8) return chars.slice(0, 8).join('') + '…'
  return name
}

// 折后价（给客户的最终单价）= 原价 ×(100+折扣)/100 + 客户加价，保留 2 位小数。
// 佣金比例为内部结算用、客户不可见，不计入折后价。
function finalPrice(ln: QuoteLine): number {
  const base = ln.price * (100 + (ln.discount || 0)) / 100 + (ln.cust_zhekou_jiajia || 0)
  return Math.round((base + Number.EPSILON) * 100) / 100
}

function onCustInput() {
  const key = custKeyword.value.trim()
  custId.value = 0
  if (key.length < 1) { custMatches.value = []; return }
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
  custId.value = c.id
  custName.value = c.name
  custKeyword.value = c.name
  custMatches.value = []
  // 若已选产品，刷新折扣
  if (itemId.value > 0) loadDiscount()
}

function onItemInput() {
  const key = itemKw.value.trim()
  if (key.length < 2) { itemMatches.value = []; return }
  const out: Item[] = []
  for (const it of itemList.value) {
    if (it.itemname.indexOf(key) !== -1 || it.itemcode.indexOf(key) !== -1) {
      out.push(it)
      if (out.length >= 80) break
    }
  }
  itemMatches.value = out
}

async function selectItem(it: Item) {
  itemId.value = it.id
  itemKw.value = it.itemname
  itemDetail.value = it
  itemMatches.value = []
  await loadDiscount()
}

// 选中客户+产品后，加载已有折扣参数（等价确认产品后回填折扣卡）
async function loadDiscount() {
  if (custId.value <= 0 || itemId.value <= 0) {
    discountForm.discount = 0
    discountForm.cust_yongjin_p = 0
    discountForm.cust_zhekou_jiajia = 0
    return
  }
  const { data } = await client.get('/discounts', {
    params: { cust_id: custId.value, item_id: itemId.value },
  })
  discountForm.discount = data.discount
  discountForm.cust_yongjin_p = data.cust_yongjin_p
  discountForm.cust_zhekou_jiajia = data.cust_zhekou_jiajia
}

async function saveDiscount() {
  errorMsg.value = ''
  infoMsg.value = ''
  if (custId.value <= 0 || itemId.value <= 0) {
    errorMsg.value = `保存折扣失败：缺少客户或产品信息。 (cust_id=${custId.value}, item_id=${itemId.value})`
    return
  }
  try {
    const { data } = await client.post('/discounts', {
      cust_id: custId.value,
      item_id: itemId.value,
      discount: discountForm.discount || 0,
      cust_yongjin_p: discountForm.cust_yongjin_p || 0,
      cust_zhekou_jiajia: discountForm.cust_zhekou_jiajia || 0,
    })
    infoMsg.value = data.message
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || '保存折扣失败'
  }
}

async function addToTemp() {
  errorMsg.value = ''
  infoMsg.value = ''
  if (custId.value <= 0 || itemId.value <= 0) {
    errorMsg.value = '增加临时行失败：缺少客户或产品信息。'
    return
  }
  try {
    const { data } = await client.post('/quote/prepare-line', {
      cust_id: custId.value,
      item_id: itemId.value,
      cust_po: addForm.cust_po,
      cust_kuanhao: addForm.cust_kuanhao,
      color: addForm.color,
      qty: addForm.qty || 0,
    })
    if (!data.ok) {
      infoMsg.value = data.message // 数量为 0 等
      return
    }
    quote.addLine(data.line as QuoteLine)
    infoMsg.value = data.message
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || '增加临时行失败'
  }
}

function clearTemp() {
  quote.clear()
  infoMsg.value = '临时列表已清空'
}

function downloadBlob(data: BlobPart, headers: Record<string, any>, fallback: string) {
  let filename = fallback
  const disp = headers['content-disposition'] as string | undefined
  if (disp) {
    // 优先解析 RFC 5987 的 filename*，否则退回普通 filename
    const mStar = /filename\*=UTF-8''([^;]+)/i.exec(disp)
    const m = /filename="?([^";]+)"?/.exec(disp)
    if (mStar) filename = decodeURIComponent(mStar[1])
    else if (m) filename = decodeURIComponent(m[1])
  }
  const url = window.URL.createObjectURL(new Blob([data]))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

async function importToPc() {
  importing.value = true
  importResult.value = null
  const smap = serialMap(previewLines.value)
  const linesWithSerial = previewLines.value.map(ln => ({ ...ln, serial_no: smap.get(ln.cust_name)! }))
  try {
    const { data } = await client.post('/quote/submit-to-pc', { lines: linesWithSerial }, { timeout: 120000 })
    const results: any[] = data.results || []
    const allOk = results.every((r: any) => r.ok)
    const msgs = results.map((r: any) =>
      r.ok
        ? `✓ ${r.cust_name}（流水号 ${r.order_po}）：${r.submit?.err ?? '录入成功'}`
        : `✗ ${r.cust_name}：${r.message ?? JSON.stringify(r.submit)}`
    )
    importResult.value = { ok: allOk, msg: msgs.join('\n') }
  } catch (e: any) {
    importResult.value = { ok: false, msg: e?.response?.data?.detail || '提交失败，请检查网络或 PC 端配置' }
  } finally {
    importing.value = false
  }
}

function openPreview(target: 'batch' | 'coats') {
  errorMsg.value = ''
  if (quote.lines.length === 0) {
    errorMsg.value = '没有临时报价行，无法导出'
    return
  }
  previewTarget.value = target
  previewLines.value = quote.lines.map(ln => ({ ...ln }))
  importResult.value = null
  showPreview.value = true
}

async function confirmExport() {
  errorMsg.value = ''
  showPreview.value = false
  const smap = serialMap(previewLines.value)
  const linesWithSerial = previewLines.value.map(ln => ({ ...ln, serial_no: smap.get(ln.cust_name)! }))
  try {
    if (previewTarget.value === 'batch') {
      const resp = await client.post('/quote/export-batch', { lines: linesWithSerial }, { responseType: 'blob', timeout: 60000 })
      downloadBlob(resp.data, resp.headers, '批量导入.xlsx')
    } else {
      const resp = await client.post(
        '/quote/export-coats',
        { lines: linesWithSerial, ship_to: coatsForm.ship_to, buyer: coatsForm.buyer },
        { responseType: 'blob', timeout: 60000 },
      )
      downloadBlob(resp.data, resp.headers, '高士下单.xlsx')
    }
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || '导出失败'
  }
}

function onLogout() {
  auth.logout()
  router.push({ name: 'login' })
}

onMounted(async () => {
  const [cust, items, seq] = await Promise.all([
    client.get('/customers'),
    client.get('/items'),
    client.get('/quote/next-seq'),
  ])
  custList.value = cust.data
  itemList.value = items.data
  nextSeq.value = seq.data.next_seq
})
</script>

<style scoped>
.header-user { background:#0052cc; color:#fff; padding:6px 12px; }
.header-user span { margin-right:8px; }
.header-user a { display:inline-block; padding:2px 6px; margin-left:8px; border-radius:4px; color:#fff !important; }
.btn-green { background:#28a745; }
.btn-blue { background:#007bff; }
.btn-red { background:#dc3545; }
.container { padding:10px; }
.section { background:#fff; margin-bottom:10px; border-radius:8px; padding:10px 12px; box-shadow:0 1px 3px rgba(0,0,0,0.05); }
.section-title { font-weight:bold; margin-bottom:6px; font-size:15px; }
.form-row { margin-bottom:8px; }
.relative { position:relative; }
.form-row input { width:100%; padding:6px 8px; border:1px solid #ccc; border-radius:4px; font-size:14px; box-sizing:border-box; }
.hint { font-size:12px; color:#888; }
.select-list { border:1px solid #ddd; border-top:none; border-radius:0 0 4px 4px; max-height:180px; overflow-y:auto; background:#fff; position:absolute; left:0; right:0; z-index:20; }
.select-item { padding:6px 8px; font-size:13px; border-bottom:1px solid #f3f3f3; cursor:pointer; }
.select-item:hover { background:#e8f0fe; }
.qo-card { background:#fff; border-radius:4px; padding:12px 14px 16px; margin-bottom:10px; box-shadow:0 1px 3px rgba(0,0,0,0.05); }
.qo-card-title { font-size:15px; font-weight:bold; margin-bottom:4px; }
.qo-card-sub { font-size:12px; color:#666; line-height:1.5; margin-bottom:8px; }
.qo-section-title { font-size:14px; font-weight:bold; margin-bottom:6px; }
.qo-grid { display:flex; flex-wrap:wrap; margin:0 -4px 6px; }
.qo-grid-2 .qo-field { width:50%; }
.qo-field { padding:0 4px; margin-bottom:8px; box-sizing:border-box; }
.qo-field label { display:block; font-size:13px; margin-bottom:4px; }
.qo-field input { width:100%; padding:6px 8px; font-size:14px; border:1px solid #ccc; border-radius:3px; box-sizing:border-box; }
.qo-field-hint { font-size:11px; color:#999; margin-top:2px; }
.qo-field-hint-strong { color:#c0392b; }
.qo-btn-row { margin-top:10px; text-align:left; }
.btn { display:inline-block; padding:8px 12px; border-radius:4px; border:none; font-size:14px; margin-right:8px; }
.btn-primary { background:#0052cc; color:#fff; }
.btn-green2 { background:#28a745; color:#fff; }
.btn-danger { background:#d93025; color:#fff; }
.table-wrap { overflow-x:auto; margin-top:6px; }
.temp-table { width:100%; border-collapse:collapse; font-size:12px; }
.temp-table th, .temp-table td { border:1px solid #ddd; padding:4px 3px; text-align:center; }
.temp-table th { background:#fafafa; }
.icon-del { color:#d93025; font-size:14px; cursor:pointer; }
.bottom-actions { margin-top:10px; }
.msg-error { background:#fce8e6; color:#c5221f; padding:8px 10px; font-size:13px; margin-bottom:10px; border-radius:4px; }
.msg-info { background:#e8f0fe; color:#174ea6; padding:8px 10px; font-size:13px; margin-bottom:10px; border-radius:4px; }
.small-text { font-size:12px; color:#666; }
/* 预览弹层 */
.preview-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.55); z-index:100; display:flex; align-items:flex-start; justify-content:center; padding:20px 0; overflow-y:auto; }
.preview-dialog { background:#fff; border-radius:8px; width:98vw; max-width:1100px; padding:16px; box-shadow:0 4px 24px rgba(0,0,0,0.2); }
.preview-title { font-size:15px; font-weight:bold; margin-bottom:4px; }
.preview-hint { font-size:12px; color:#888; font-weight:normal; margin-left:6px; }
.preview-scroll { overflow-x:auto; margin:10px 0; }
.preview-table { width:100%; border-collapse:collapse; font-size:12px; }
.preview-table th, .preview-table td { border:1px solid #ddd; padding:3px 4px; text-align:center; white-space:nowrap; }
.preview-table th { background:#f0f4ff; }
.cell-input { width:80px; padding:2px 4px; border:1px solid #bbb; border-radius:3px; font-size:12px; text-align:center; }
.cell-num { width:60px; }
.preview-actions { margin-top:12px; display:flex; gap:10px; }
.btn-cancel { background:#888; color:#fff; }
.btn-import { background:#e67e22; color:#fff; }
.btn-import:disabled { opacity:0.6; }
</style>
