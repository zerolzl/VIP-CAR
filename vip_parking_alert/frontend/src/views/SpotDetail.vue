<template>
  <div class="spot-detail-page">
    <el-page-header @back="goBack" title="返回" :content="`车位详情 - ${spotInfo.spot_number || ''}`" style="margin-bottom: 20px;" />

    <!-- 车位基本信息 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <span>基本信息</span>
      </template>
      <el-descriptions :column="2" border v-loading="loadingSpot">
        <el-descriptions-item label="车位编号">{{ spotInfo.spot_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="所属人">{{ spotInfo.owner || '-' }}</el-descriptions-item>
        <el-descriptions-item label="允许车牌" :span="2">
          <el-tag
            v-for="(plate, idx) in (spotInfo.allowed_plates || [])"
            :key="idx"
            size="small"
            style="margin-right: 4px; margin-bottom: 2px;"
          >
            {{ plate }}
          </el-tag>
          <span v-if="!spotInfo.allowed_plates || spotInfo.allowed_plates.length === 0" style="color: #999;">无</span>
        </el-descriptions-item>
        <el-descriptions-item label="监控状态">
          <el-tag :type="spotInfo.monitoring ? 'success' : 'info'" size="small">
            {{ spotInfo.monitoring ? '监控中' : '未监控' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ spotInfo.created_at || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 通知配置列表 -->
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>通知配置</span>
          <el-button type="primary" size="small" :icon="Plus" @click="openNotifyForm(null)">新增通知配置</el-button>
        </div>
      </template>

      <el-table :data="notifyConfigs" stripe v-loading="loadingConfigs" style="width: 100%;">
        <el-table-column label="通知类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.notify_type === 'sms' ? '' : 'warning'" size="small">
              {{ row.notify_type === 'sms' ? '短信' : 'Webhook' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="目标" min-width="200" />
        <el-table-column prop="contact_name" label="关联联系人" width="120">
          <template #default="{ row }">
            {{ row.contact_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="启用状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openNotifyForm(row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="handleDeleteConfig(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 通知配置弹窗 -->
    <NotifyConfigForm
      v-model:visible="notifyFormVisible"
      :config="editingConfig"
      :spot-id="spotId"
      @saved="loadNotifyConfigs"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getSpots, updateSpot } from '../api/spots'
import { getNotifyConfigs, deleteNotifyConfig } from '../api/notifyConfigs'
import NotifyConfigForm from '../components/NotifyConfigForm.vue'

const route = useRoute()
const router = useRouter()

const spotId = Number(route.params.id)
const loadingSpot = ref(false)
const loadingConfigs = ref(false)
const spotInfo = ref({})
const notifyConfigs = ref([])

const notifyFormVisible = ref(false)
const editingConfig = ref(null)

function goBack() {
  router.push('/spots')
}

async function loadSpotInfo() {
  loadingSpot.value = true
  try {
    const res = await getSpots({ page: 1, page_size: 1000 })
    const spots = res.items || res || []
    const spot = spots.find(s => s.id === spotId)
    if (spot) {
      spotInfo.value = spot
    } else {
      ElMessage.error('未找到该车位')
    }
  } catch (e) {
    // error handled by interceptor
  } finally {
    loadingSpot.value = false
  }
}

async function loadNotifyConfigs() {
  loadingConfigs.value = true
  try {
    const res = await getNotifyConfigs(spotId)
    notifyConfigs.value = res.items || res || []
  } catch (e) {
    // error handled by interceptor
  } finally {
    loadingConfigs.value = false
  }
}

function openNotifyForm(config) {
  editingConfig.value = config
  notifyFormVisible.value = true
}

async function handleDeleteConfig(row) {
  try {
    await ElMessageBox.confirm(
      '确定要删除该通知配置吗？',
      '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
    await deleteNotifyConfig(row.id)
    ElMessage.success('删除成功')
    loadNotifyConfigs()
  } catch (e) {
    // cancelled or error
  }
}

onMounted(() => {
  loadSpotInfo()
  loadNotifyConfigs()
})
</script>

<style scoped>
.spot-detail-page {
  padding: 0;
}
</style>
