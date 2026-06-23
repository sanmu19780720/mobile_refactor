import { defineStore } from 'pinia'

// 一条临时报价行，字段与后端 QuoteLine 对齐
export interface QuoteLine {
  cust_name: string
  cust_po: string
  cust_kuanhao: string
  itemname: string
  itemcode: string
  huohao: string
  cudu: string
  color: string
  qty: number
  price: number
  discount: number
  cust_yongjin_p: number
  cust_zhekou_jiajia: number
}

interface QuoteState {
  lines: QuoteLine[]
}

export const useQuoteStore = defineStore('quote', {
  state: (): QuoteState => ({
    lines: [],
  }),
  actions: {
    addLine(line: QuoteLine) {
      this.lines.push(line)
    },
    deleteLine(index: number) {
      if (index >= 0 && index < this.lines.length) {
        this.lines.splice(index, 1)
      }
    },
    clear() {
      this.lines = []
    },
  },
  // 等价原 $_SESSION['quote_temp']，改为前端持久化到 localStorage
  persist: true,
})
