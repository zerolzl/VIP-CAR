<template>
  <div class="plate-tag-input">
    <el-tag
      v-for="(plate, index) in modelValue"
      :key="index"
      closable
      :disable-transitions="false"
      @close="removeTag(index)"
      style="margin-right: 6px; margin-bottom: 4px;"
    >
      {{ plate }}
    </el-tag>
    <el-input
      v-if="inputVisible"
      ref="inputRef"
      v-model="inputValue"
      size="small"
      style="width: 140px;"
      placeholder="输入车牌号"
      @keyup.enter="addTag"
      @blur="addTag"
    />
    <el-button
      v-else
      size="small"
      @click="showInput"
      :icon="Plus"
    >
      添加车牌
    </el-button>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { Plus } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const inputVisible = ref(false)
const inputValue = ref('')
const inputRef = ref(null)

function showInput() {
  inputVisible.value = true
  nextTick(() => {
    inputRef.value?.input?.focus()
  })
}

function addTag() {
  const val = inputValue.value.trim()
  if (val && !props.modelValue.includes(val)) {
    emit('update:modelValue', [...props.modelValue, val])
  }
  inputVisible.value = false
  inputValue.value = ''
}

function removeTag(index) {
  const newList = [...props.modelValue]
  newList.splice(index, 1)
  emit('update:modelValue', newList)
}
</script>

<style scoped>
.plate-tag-input {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
</style>
