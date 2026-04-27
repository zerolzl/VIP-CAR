<template>
  <div class="dashboard">
    <h2 style="margin-bottom: 20px;">仪表盘</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 24px;">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon :size="24"><Monitor /></el-icon>
              <span>监控中车位数</span>
            </div>
          </template>
          <div class="card-value">{{ stats.monitoringCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon :size="24"><WarningFilled /></el-icon>
              <span>当前未解决告警</span>
            </div>
          </template>
          <div class="card-value alert-value">{{ stats.unresolvedCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon :size="24"><Bell /></el-icon>
              <span>今日告警总数</span>
            </div>
          </template>
          <div class="card-value">{{ stats.todayCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon :size="24"><CircleCheck /></el-icon>
              <span>已解决数</span>
            </div>
          </template>
          <div class="card-value success-value">{{ stats.resolvedCount }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近告警列表 -->
    <el-card style="margin-bottom: 24px;">
      <template #header>
        <span>最近告警（最近10条）</span>
      </template>
      <el-table :data="recentAlerts" stripe style="width: 100%;" v-loading="loadingAlerts">
        <el-table-column prop="spot_id" label="车位编号" width="120" />
        <el-table-column prop="plate_number" label="车牌号" width="140" />
        <el-table-column prop="channel" label="发送通道" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.channel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sent_at" label="发送时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.sent_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.resolved ? 'success' : 'danger'" size="small">
              {{ row.resolved ? '已解决' : '未解决' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resolved_at" label="恢复时间">
          <template #default="{ row }">
            {{ row.resolved_at ? formatTime(row.resolved_at) : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 系统状态 -->
    <el-card>
      <template #header>
        <span>系统状态</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="调度器状态">
          <el-tag :type="systemStatus.scheduler_running ? 'success' : 'danger'" size="small">
            {{ systemStatus.scheduler_running ? '运行中' : '已停止' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="上次巡检时间">
          {{ systemStatus.last_inspection || '暂无' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getSpots } from '../api/spots'
import { getAlerts } from '../api/alerts'
import { getHealth } from '../api/settings'

const loadingAlerts = ref(false)
const recentAlerts = ref([])

const stats = reactive({
  monitoringCount: 0,
  unresolvedCount: 0,
  todayCount: 0,
  resolvedCount: 0
})

const systemStatus = reactive({
  scheduler_running: false,
  last_inspection: ''
})

function formatTime(timeStr) {
  if (!timeStr) return '-'
  return timeStr.replace('T', ' ').substring(0, 19)
}

async function loadDashboardData() {
  try {
    // 加载车位数据
    const spotsRes = await getSpots({ page: 1, page_size: 1, monitoring: true })
    const allSpotsRes = await getSpots({ page: 1, page_size: 1 })
    stats.monitoringCount = spotsRes.total ?? (Array.isArray(spotsRes) ? spotsRes.length : 0)

    // 加载告警数据
    loadingAlerts.value = true
    const alertsRes = await getAlerts({ page: 1, page_size: 10 })
    const alerts = alertsRes.data || alertsRes.items || alertsRes || []
    recentAlerts.value = alerts.slice(0, 10)

    // 统计告警
    const today = new Date().toISOString().slice(0, 10)
    const allAlertsRes = await getAlerts({ page: 1, page_size: 1000 })
    const allAlerts = allAlertsRes.data || allAlertsRes.items || allAlertsRes || []
    stats.unresolvedCount = allAlerts.filter(a => !a.resolved).length
    stats.todayCount = allAlerts.filter(a => (a.sent_at || '').startsWith(today)).length
    stats.resolvedCount = allAlerts.filter(a => a.resolved).length
  } catch (e) {
    // error handled by interceptor
  } finally {
    loadingAlerts.value = false
  }
}

async function loadSystemStatus() {
  try {
    const res = await getHealth()
    Object.assign(systemStatus, {
      scheduler_running: res.scheduler_running ?? false,
      last_inspection: res.last_inspection || ''
    })
  } catch (e) {
    // error handled by interceptor
  }
}

onMounted(() => {
  loadDashboardData()
  loadSystemStatus()
})
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}
.card-value {
  font-size: 32px;
  font-weight: bold;
  text-align: center;
  color: #409eff;
}
.alert-value {
  color: #f56c6c;
}
.success-value {
  color: #67c23a;
}
</style>
