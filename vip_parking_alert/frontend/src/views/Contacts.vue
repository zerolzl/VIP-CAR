<template>
  <div class="contacts-page">
    <h2 style="margin-bottom: 20px;">通讯录管理</h2>

    <!-- 顶部操作 -->
    <div style="margin-bottom: 16px;">
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增联系人</el-button>
    </div>

    <!-- 联系人表格 -->
    <el-table :data="contactList" stripe v-loading="loading" style="width: 100%;">
      <el-table-column prop="name" label="姓名" width="180" />
      <el-table-column prop="phone" label="手机号" width="180" />
      <el-table-column label="启用状态" width="120" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.enabled"
            @change="(val) => toggleEnabled(row, val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="openDialog(row)">编辑</el-button>
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
        @size-change="fetchContacts"
        @current-change="fetchContacts"
      />
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingContact ? '编辑联系人' : '新增联系人'"
      width="450px"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="姓名" prop="name">
          <el-input v-model="formData.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="formData.enabled" />
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getContacts, createContact, updateContact, deleteContact } from '../api/contacts'

const loading = ref(false)
const contactList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const dialogVisible = ref(false)
const editingContact = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const defaultFormData = () => ({
  name: '',
  phone: '',
  enabled: true
})

const formData = ref(defaultFormData())

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }]
}

async function fetchContacts() {
  loading.value = true
  try {
    const res = await getContacts({
      page: currentPage.value,
      page_size: pageSize.value
    })
    contactList.value = res.data || res.items || res || []
    total.value = res.total ?? contactList.value.length
  } catch (e) {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function openDialog(contact) {
  if (contact) {
    editingContact.value = contact
    formData.value = {
      name: contact.name || '',
      phone: contact.phone || '',
      enabled: contact.enabled !== false
    }
  } else {
    editingContact.value = null
    formData.value = defaultFormData()
  }
  dialogVisible.value = true
}

function resetForm() {
  formData.value = defaultFormData()
  editingContact.value = null
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
      name: formData.value.name,
      phone: formData.value.phone,
      enabled: formData.value.enabled
    }

    if (editingContact.value) {
      await updateContact(editingContact.value.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createContact(payload)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    fetchContacts()
  } catch (e) {
    // error handled by interceptor
  } finally {
    submitting.value = false
  }
}

async function toggleEnabled(row, val) {
  try {
    await updateContact(row.id, { ...row, enabled: val })
    ElMessage.success(val ? '已启用' : '已禁用')
    fetchContacts()
  } catch (e) {
    // error handled by interceptor
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除联系人「${row.name}」吗？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
    await deleteContact(row.id)
    ElMessage.success('删除成功')
    fetchContacts()
  } catch (e) {
    // cancelled or error
  }
}

onMounted(() => {
  fetchContacts()
})
</script>

<style scoped>
.contacts-page {
  padding: 0;
}
</style>
