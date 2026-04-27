<template>
  <div class="alert-logs-page">
    <h2 style="margin-bottom: 20px;">告警日志</h2>

    <!-- 筛选栏 -->
    <el-row :gutter="16" style="margin-bottom: 16px;" align="middle">
      <el-col :span="4">
        <el-input
          v-model="filters.spot_number"
          placeholder="车位编号"
          clearable
          @clear="fetchAlerts"
          @keyup.enter="fetchAlerts"
        />
      </el-col>
      <el-col :span="4">
        <el-input
          v-model="filters.plate_number"
          placeholder="车牌号"
          clearable
          @clear="fetchAlerts"
          @keyup.enter="fetchAlerts"
        />
      </el-col>
      <el-col :span="3">
        <el-select v-model="filters.resolved" placeholder="解决状态" clearable style="width: 100%;" @change="fetchAlerts">
          <el-option label="全部" :value="''" />
          <el-option label="未解决" :value="false" />
          <el-option label="已解决" :value="true" />
        </el-select>
      </el-col>
      <el-col :span="7">
        <el-date-picker
          v-model="filters.dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          value-format="YYYY-MM-DDTHH:mm:ss"
          style="width: 100%;"
          @change="fetchAlerts"
        />
      </el-col>
      <el-col :span="2">
        <el-button type="primary" :icon="Search" @click="fetchAlerts">查询</el-button>
      </el-col>
    </el-row>

    <!-- 告警表格 -->
    <el-table :data="alertList" stripe v-loading="loading" style="width: 100%;">
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
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.resolved ? 'success' : 'danger'" size="small">
            {{ row.resolved ? '已解决' : '未解决' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="resolved_at" label="恢复时间" min-width="180">
        <template #default="{ row }">
          {{ row.resolved_at ? formatTime(row.resolved_at) : '-' }}
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchAlerts"
        @current-change="fetchAlerts"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getAlerts } from '../api/alerts'

const loading = ref(false)
const alertList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  spot_number: '',
  plate_number: '',
  resolved: '',
  dateRange: null
})

function formatTime(timeStr) {
  if (!timeStr) return '-'
  return timeStr.replace('T', ' ').substring(0, 19)
}

async function fetchAlerts() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filters.spot_number) {
      params.spot_number = filters.spot_number
    }
    if (filters.plate_number) {
      params.plate_number = filters.plate_number
    }
    if (filters.resolved !== '' && filters.resolved !== null && filters.resolved !== undefined) {
      params.resolved = filters.resolved
    }
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_time = filters.dateRange[0]
      params.end_time = filters.dateRange[1]
    }

    const res = await getAlerts(params)
    alertList.value = res.data || res.items || res || []
    total.value = res.total ?? alertList.value.length
  } catch (e) {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAlerts()
})
</script>

<style scoped>
.alert-logs-page {
  padding: 0;
}
</style>
