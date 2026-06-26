import { defineStore } from 'pinia'

export interface OrderItem {
  order_id: number
  orders_po: string
  order_input_date: string
  order_expect_date: string
  order_status: number | string
  status_text: string
  cust_name: string
  cust_short: string
  recv_man: string
  recv_call: string
  cust_address: string
  total_qty: number
  cust_po_list: string
  cust_kuanhao_list: string
  last_chuhuo_date: string
  wuliu_ids: string
}

interface OrderSearchState {
  custKeyword: string
  custId: number
  keyword: string
  dateFrom: string
  dateTo: string
  orders: OrderItem[]
}

export const useOrderSearchStore = defineStore('orderSearch', {
  state: (): OrderSearchState => ({
    custKeyword: '',
    custId: 0,
    keyword: '',
    dateFrom: '',
    dateTo: '',
    orders: [],
  }),
  actions: {
    reset() {
      this.custKeyword = ''
      this.custId = 0
      this.keyword = ''
      this.dateFrom = ''
      this.dateTo = ''
      this.orders = []
    },
  },
  // 离开详情页返回时保留查询条件与结果；刷新页面也可恢复
  persist: true,
})
