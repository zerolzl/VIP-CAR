<template>
  <div class="spots-page">
    <h2 style="margin-bottom: 20px;">车位管理</h2>

    <!-- 搜索栏 -->
    <el-row :gutter="16" style="margin-bottom: 16px;" align="middle">
      <el-col :span="6">
        <el-input
          v-model="searchQuery"
          placeholder="搜索车位编号/所属人"
          clearable
          :prefix-icon="Search"
          @clear="fetchSpots"
          @keyup.enter="fetchSpots"
        />
      </el-col>
      <el-col :span="4">
        <el-select v-model="statusFilter" placeholder="监控状态" clearable style="width: 100%;" @change="fetchSpots">
          <el-option label="监控中" :value="true" />
          <el-option label="未监控" :value="false" />
        </el-select>
      </el-col>
      <el-col :span="2">
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增车位</el-button>
      </el-col>
    </el-row>

    <!-- 车位表格 -->
    <el-table :data="spotList" stripe v-loading="loading" style="width: 100%;">
      <el-table-column prop="spot_number" label="车位编号" width="140" />
      <el-table-column prop="owner" label="所属人" width="140" />
      <el-table-column label="允许车牌" min-width="200">
        <template #default="{ row }">
          <el-tag
            v-for="(plate, idx) in (row.allowed_plates || [])"
            :key="idx"
            size="small"
            style="margin-right: 4px; margin-bottom: 2px;"
          >
            {{ plate }}
          </el-tag>
          <span v-if="!row.allowed_plates || row.allowed_plates.length === 0" style="color: #999;">无</span>
        </template>
      </el-table-column>
      <el-table-column label="监控状态" width="100" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.monitoring"
            @change="(val) => toggleMonitoring(row, val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="primary" link @click="goDetail(row.id)">详情</el-button>
          <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchSpots"
        @current-change="fetchSpots"
      />
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingSpot ? '编辑车位' : '新增车位'"
      width="520px"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="车位编号" prop="spot_number">
          <el-input v-model="formData.spot_number" placeholder="请输入车位编号" />
        </el-form-item>
        <el-form-item label="所属人" prop="owner">
          <el-input v-model="formData.owner" placeholder="请输入所属人" />
        </el-form-item>
        <el-form-item label="允许车牌">
          <PlateTagInput v-model="formData.allowed_plates" />
        </el-form-item>
        <el-form-item label="监控状态">
          <el-switch v-model="formData.monitoring" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getSpots, createSpot, updateSpot, deleteSpot } from '../api/spots'
import PlateTagInput from '../components/PlateTagInput.vue'

const router = useRouter()

const loading = ref(false)
const spotList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const statusFilter = ref(null)

const dialogVisible = ref(false)
const editingSpot = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const defaultFormData = () => ({
  spot_number: '',
  owner: '',
  allowed_plates: [],
  monitoring: true
})

const formData = ref(defaultFormData())

const rules = {
  spot_number: [{ required: true, message: '请输入车位编号', trigger: 'blur' }],
  owner: [{ required: true, message: '请输入所属人', trigger: 'blur' }]
}

async function fetchSpots() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    if (statusFilter.value !== null && statusFilter.value !== undefined && statusFilter.value !== '') {
      params.monitoring = statusFilter.value
    }
    const res = await getSpots(params)
    spotList.value = res.data || res.items || res || []
    total.value = res.total ?? spotList.value.length
  } catch (e) {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function openDialog(spot) {
  if (spot) {
    editingSpot.value = spot
    formData.value = {
      spot_number: spot.spot_number || '',
      owner: spot.owner || '',
      allowed_plates: [...(spot.allowed_plates || [])],
      monitoring: spot.monitoring !== false
    }
  } else {
    editingSpot.value = null
    formData.value = defaultFormData()
  }
  dialogVisible.value = true
}

function resetForm() {
  formData.value = defaultFormData()
  editingSpot.value = null
  formRef.value?.resetFields()
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const payload = {
      spot_number: formData.value.spot_number,
      owner: formData.value.owner,
      allowed_plates: formData.value.allowed_plates,
      monitoring: formData.value.monitoring
    }

    if (editingSpot.value) {
      await updateSpot(editingSpot.value.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createSpot(payload)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    fetchSpots()
  } catch (e) {
    // error handled by interceptor
  } finally {
    submitting.value = false
  }
}

async function toggleMonitoring(row, val) {
  try {
    await updateSpot(row.id, { ...row, monitoring: val })
    ElMessage.success(val ? '已开启监控' : '已关闭监控')
    fetchSpots()
  } catch (e) {
    // error handled by interceptor
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除车位「${row.spot_number}」吗？此操作不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
    await deleteSpot(row.id)
    ElMessage.success('删除成功')
    fetchSpots()
  } catch (e) {
    // cancelled or error
  }
}

function goDetail(id) {
  router.push(`/spots/${id}`)
}

onMounted(() => {
  fetchSpots()
})
</script>

<style scoped>
.spots-page {
  padding: 0;
}
</style>
