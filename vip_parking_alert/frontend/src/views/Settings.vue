<template>
  <div class="settings-page">
    <h2 style="margin-bottom: 20px;">系统设置</h2>

    <el-tabs v-model="activeTab">
      <!-- Tab1: 外部数据库 -->
      <el-tab-pane label="外部数据库" name="database">
        <el-card>
          <el-form
            ref="dbFormRef"
            :model="dbForm"
            :rules="dbRules"
            label-width="120px"
            style="max-width: 600px;"
          >
            <el-form-item label="名称" prop="name">
              <el-input v-model="dbForm.name" placeholder="请输入数据源名称" />
            </el-form-item>
            <el-form-item label="类型" prop="db_type">
              <el-select v-model="dbForm.db_type" placeholder="请选择数据库类型" style="width: 100%;">
                <el-option label="MySQL" value="mysql" />
                <el-option label="PostgreSQL" value="postgresql" />
                <el-option label="SQL Server" value="mssql" />
                <el-option label="SQLite" value="sqlite" />
              </el-select>
            </el-form-item>
            <el-form-item label="主机" prop="host">
              <el-input v-model="dbForm.host" placeholder="请输入主机地址" />
            </el-form-item>
            <el-form-item label="端口" prop="port">
              <el-input-number v-model="dbForm.port" :min="1" :max="65535" style="width: 100%;" />
            </el-form-item>
            <el-form-item label="数据库名" prop="database">
              <el-input v-model="dbForm.database" placeholder="请输入数据库名" />
            </el-form-item>
            <el-form-item label="用户名" prop="username">
              <el-input v-model="dbForm.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="dbForm.password" type="password" show-password placeholder="请输入密码" />
            </el-form-item>
            <el-form-item label="启用">
              <el-switch v-model="dbForm.enabled" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="dbSaving" @click="saveDbConfig">保存</el-button>
              <el-button :loading="dbTesting" @click="testDbConnection">测试连接</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- Tab2: 短信网关 -->
      <el-tab-pane label="短信网关" name="sms">
        <el-card>
          <el-form
            ref="smsFormRef"
            :model="smsForm"
            :rules="smsRules"
            label-width="120px"
            style="max-width: 600px;"
          >
            <el-form-item label="名称" prop="name">
              <el-input v-model="smsForm.name" placeholder="请输入网关名称" />
            </el-form-item>
            <el-form-item label="URL" prop="url">
              <el-input v-model="smsForm.url" placeholder="请输入网关URL" />
            </el-form-item>
            <el-form-item label="Token" prop="token">
              <el-input v-model="smsForm.token" type="password" show-password placeholder="请输入Token" />
            </el-form-item>
            <el-form-item label="发送方标识" prop="sender_id">
              <el-input v-model="smsForm.sender_id" placeholder="请输入发送方标识" />
            </el-form-item>
            <el-form-item label="启用">
              <el-switch v-model="smsForm.enabled" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="smsSaving" @click="saveSmsConfig">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- Tab3: 系统 -->
      <el-tab-pane label="系统" name="system">
        <el-card>
          <el-form label-width="120px" style="max-width: 600px;">
            <el-form-item label="巡检间隔（秒）">
              <el-input-number
                v-model="inspectionInterval"
                :min="10"
                :max="3600"
                :step="10"
                style="width: 100%;"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="warning" :loading="reloading" @click="handleReloadConfig">
                立即生效
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getExternalDb,
  updateExternalDb,
  testExternalDb,
  getSmsGateway,
  updateSmsGateway,
  reloadConfig
} from '../api/settings'

const activeTab = ref('database')

// ===== 外部数据库 =====
const dbFormRef = ref(null)
const dbSaving = ref(false)
const dbTesting = ref(false)

const defaultDbForm = () => ({
  name: '',
  db_type: 'mysql',
  host: '',
  port: 3306,
  database: '',
  username: '',
  password: '',
  enabled: false
})

const dbForm = ref(defaultDbForm())

const dbRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  db_type: [{ required: true, message: '请选择数据库类型', trigger: 'change' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
  database: [{ required: true, message: '请输入数据库名', trigger: 'blur' }]
}

// ===== 短信网关 =====
const smsFormRef = ref(null)
const smsSaving = ref(false)

const defaultSmsForm = () => ({
  name: '',
  url: '',
  token: '',
  sender_id: '',
  enabled: false
})

const smsForm = ref(defaultSmsForm())

const smsRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  url: [{ required: true, message: '请输入URL', trigger: 'blur' }]
}

// ===== 系统 =====
const inspectionInterval = ref(60)
const reloading = ref(false)

// ===== 数据加载 =====
async function loadDbConfig() {
  try {
    const res = await getExternalDb()
    dbForm.value = {
      name: res.name || '',
      db_type: res.db_type || 'mysql',
      host: res.host || '',
      port: res.port || 3306,
      database: res.database || '',
      username: res.username || '',
      password: res.password || '',
      enabled: res.enabled || false
    }
  } catch (e) {
    // error handled by interceptor
  }
}

async function loadSmsConfig() {
  try {
    const res = await getSmsGateway()
    smsForm.value = {
      name: res.name || '',
      url: res.url || '',
      token: res.token || '',
      sender_id: res.sender_id || '',
      enabled: res.enabled || false
    }
  } catch (e) {
    // error handled by interceptor
  }
}

// ===== 保存操作 =====
async function saveDbConfig() {
  try {
    await dbFormRef.value?.validate()
  } catch {
    return
  }

  dbSaving.value = true
  try {
    await updateExternalDb(dbForm.value)
    ElMessage.success('外部数据库配置已保存')
  } catch (e) {
    // error handled by interceptor
  } finally {
    dbSaving.value = false
  }
}

async function testDbConnection() {
  dbTesting.value = true
  try {
    await testExternalDb()
    ElMessage.success('连接测试成功')
  } catch (e) {
    // error handled by interceptor
  } finally {
    dbTesting.value = false
  }
}

async function saveSmsConfig() {
  try {
    await smsFormRef.value?.validate()
  } catch {
    return
  }

  smsSaving.value = true
  try {
    await updateSmsGateway(smsForm.value)
    ElMessage.success('短信网关配置已保存')
  } catch (e) {
    // error handled by interceptor
  } finally {
    smsSaving.value = false
  }
}

async function handleReloadConfig() {
  reloading.value = true
  try {
    await reloadConfig()
    ElMessage.success('配置已重新加载')
  } catch (e) {
    // error handled by interceptor
  } finally {
    reloading.value = false
  }
}

onMounted(() => {
  loadDbConfig()
  loadSmsConfig()
})
</script>

<style scoped>
.settings-page {
  padding: 0;
}
</style>
