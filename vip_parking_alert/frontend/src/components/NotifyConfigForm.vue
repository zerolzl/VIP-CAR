<template>
  <el-dialog
    :model-value="visible"
    :title="config?.id ? '编辑通知配置' : '新增通知配置'"
    width="500px"
    @update:model-value="$emit('update:visible', $event)"
    @closed="resetForm"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="通知类型" prop="notify_type">
        <el-select v-model="formData.notify_type" placeholder="请选择通知类型" style="width: 100%;">
          <el-option label="短信 (SMS)" value="sms" />
          <el-option label="Webhook" value="webhook" />
        </el-select>
      </el-form-item>

      <el-form-item label="关联联系人">
        <el-select
          v-model="formData.contact_id"
          placeholder="请选择联系人"
          clearable
          filterable
          style="width: 100%;"
          @change="onContactChange"
        >
          <el-option
            v-for="c in contactList"
            :key="c.id"
            :label="`${c.name} (${c.phone})`"
            :value="c.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="目标" prop="target">
        <el-input
          v-model="formData.target"
          :placeholder="formData.notify_type === 'webhook' ? '请输入 Webhook URL' : '请输入手机号'"
        />
      </el-form-item>

      <el-form-item label="启用" prop="enabled">
        <el-switch v-model="formData.enabled" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getContacts } from '../api/contacts'
import { createNotifyConfig, updateNotifyConfig } from '../api/notifyConfigs'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  config: {
    type: Object,
    default: null
  },
  spotId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:visible', 'saved'])

const formRef = ref(null)
const submitting = ref(false)
const contactList = ref([])

const defaultFormData = () => ({
  notify_type: 'sms',
  contact_id: null,
  target: '',
  enabled: true
})

const formData = ref(defaultFormData())

const rules = {
  notify_type: [{ required: true, message: '请选择通知类型', trigger: 'change' }],
  target: [{ required: true, message: '请输入目标', trigger: 'blur' }]
}

watch(() => props.visible, (val) => {
  if (val && props.config) {
    formData.value = {
      notify_type: props.config.notify_type || 'sms',
      contact_id: props.config.contact_id || null,
      target: props.config.target || '',
      enabled: props.config.enabled !== false
    }
  } else if (val) {
    formData.value = defaultFormData()
  }
})

onMounted(() => {
  loadContacts()
})

async function loadContacts() {
  try {
    const res = await getContacts({ page: 1, page_size: 200, enabled: true })
    contactList.value = res.items || res || []
  } catch (e) {
    // ignore
  }
}

function onContactChange(contactId) {
  if (contactId) {
    const contact = contactList.value.find(c => c.id === contactId)
    if (contact && formData.value.notify_type === 'sms') {
      formData.value.target = contact.phone || ''
    }
  }
}

function resetForm() {
  formData.value = defaultFormData()
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
      notify_type: formData.value.notify_type,
      contact_id: formData.value.contact_id,
      target: formData.value.target,
      enabled: formData.value.enabled
    }

    if (props.config?.id) {
      await updateNotifyConfig(props.config.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createNotifyConfig(props.spotId, payload)
      ElMessage.success('创建成功')
    }

    emit('update:visible', false)
    emit('saved')
  } catch (e) {
    // error handled by interceptor
  } finally {
    submitting.value = false
  }
}
</script>
