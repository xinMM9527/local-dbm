import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

export default api

// ========== Connections ==========
export interface ConnectionConfig {
  id?: string
  name: string
  type: 'mysql' | 'postgresql'
  host: string
  port: number
  username: string
  password: string
  database: string
}

export const connectionApi = {
  list: () => api.get<any, ConnectionConfig[]>('/connections'),
  create: (data: ConnectionConfig) => api.post('/connections', data),
  update: (id: string, data: ConnectionConfig) => api.put(`/connections/${id}`, data),
  delete: (id: string) => api.delete(`/connections/${id}`),
  test: (id: string) => api.post(`/connections/${id}/test`),
}

// ========== Schema ==========
export interface ColumnInfo {
  name: string
  type: string
  nullable: boolean
  default_value: string | null
  comment: string | null
  is_primary_key: boolean
  is_auto_increment: boolean
}

export interface IndexInfo {
  name: string
  columns: string[]
  unique: boolean
}

export const schemaApi = {
  databases: (connId: string) =>
    api.get<any, string[]>('/schemas/databases', { params: { conn_id: connId } }),
  tables: (connId: string, db: string) =>
    api.get<any, string[]>('/schemas/tables', { params: { conn_id: connId, database: db } }),
  columns: (connId: string, db: string, table: string) =>
    api.get<any, ColumnInfo[]>('/schemas/columns', {
      params: { conn_id: connId, database: db, table },
    }),
  indexes: (connId: string, db: string, table: string) =>
    api.get<any, IndexInfo[]>('/schemas/indexes', {
      params: { conn_id: connId, database: db, table },
    }),
}

// ========== Query ==========
export interface QueryResult {
  columns?: string[]
  rows?: any[][]
  affected_rows?: number
  message?: string
  sql: string
  duration_ms: number
}

export const queryApi = {
  execute: (connId: string, sql: string, database?: string) =>
    api.post<any, QueryResult[]>('/query/execute', { conn_id: connId, sql, database }),
  history: () => api.get<any, { sql: string; timestamp: string }[]>('/query/history'),
  clearHistory: () => api.post('/query/history/clear'),
}

// ========== DDL ==========
export interface ColumnDef {
  name: string
  type: string
  nullable: boolean
  primary_key: boolean
  auto_increment: boolean
  default_value: string | null
  comment: string | null
}

export interface CreateTableParams {
  conn_id: string
  database: string
  table: string
  columns: ColumnDef[]
  comment?: string
}

export const ddlApi = {
  createTable: (params: CreateTableParams) => api.post('/ddl/create-table', params),
  addColumn: (params: {
    conn_id: string
    database: string
    table: string
    column: ColumnDef
  }) => api.post('/ddl/add-column', params),
}

// ========== Data ==========
export const dataApi = {
  query: (connId: string, db: string, table: string, params?: { page?: number; size?: number }) =>
    api.get<any, { columns: string[]; rows: any[][]; total: number }>(`/data/${db}/${table}`, {
      params: { conn_id: connId, ...params },
    }),
  insert: (connId: string, db: string, table: string, row: Record<string, any>) =>
    api.post(`/data/${db}/${table}`, { conn_id: connId, row }),
  update: (connId: string, db: string, table: string, row: Record<string, any>) =>
    api.put(`/data/${db}/${table}`, { conn_id: connId, row }),
  delete: (connId: string, db: string, table: string, conditions: Record<string, any>) =>
    api.delete(`/data/${db}/${table}`, { data: { conn_id: connId, conditions } }),
  exportData: (connId: string, db: string, table: string, format: 'csv' | 'json') =>
    api.get(`/data/${db}/${table}/export`, {
      params: { conn_id: connId, format },
      responseType: 'blob',
    }),
}
