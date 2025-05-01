<template>
  <div class="simulation-container">


    <!-- 多任务模拟表单 -->
    <el-card class="form-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>多任务特情模拟</span>
        </div>
      </template>

      <div v-for="(_, index) in multitaskForm.position_ids" :key="index" class="task-item">
        <el-form-item label="阵位ID" :prop="'position_ids.' + index" :rules="positionRules">
          <el-input
            v-model="multitaskForm.position_ids[index]"
            placeholder="请输入阵位ID"
            @blur="() => validateMultitaskPositionId(index)">
            <template #append>
              <el-button @click="showPositionList">查看所有阵位</el-button>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="特情类型" :prop="'event_types.' + index" :rules="eventTypeRules">
          <el-select v-model="multitaskForm.event_types[index]" placeholder="请选择特情类型">
            <el-option
              v-for="item in eventTypes"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="严重程度">
          <el-slider
            v-model="multitaskForm.severities[index]"
            :min="0"
            :max="1"
            :step="0.01"
            show-input>
          </el-slider>
        </el-form-item>

        <el-form-item label="持续时间(分钟)">
          <el-input-number
            v-model="multitaskForm.durations[index]"
            :min="5"
            :max="240"
            :step="5">
          </el-input-number>
        </el-form-item>

        <el-button
          v-if="index > 0"
          type="danger"
          @click="removeTask(index)"
          circle
          icon="el-icon-minus"
          style="margin-left: 10px;"/>
      </div>

      <el-button
        type="primary"
        @click="addTask"
        icon="el-icon-plus"
        style="margin-right: 10px;">
        添加任务
      </el-button>

      <el-button
        type="success"
        @click="submitMultitaskForm"
        :loading="submittingMultitask">
        提交多任务模拟
      </el-button>
    </el-card>

    <!-- 阵位列表弹窗 -->
    <el-dialog title="所有阵位" v-model="showPositionsDialog" width="70%">
      <el-table :data="positions" border>
        <el-table-column prop="position_id" label="ID" width="100" />
        <el-table-column prop="type_identifier" label="类型名称" />
        <el-table-column prop="position_type" label="类型代码" width="100" />
        <el-table-column label="操作" width="120">
          <template #default="{row}">
            <el-button size="small" @click="selectPosition(row)">选择</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 预测结果展示 -->
    <div v-if="showResults" class="result-section">
      <el-card class="result-card">
        <template #header>
          <div class="card-header">
            <span>预测结果</span>
          </div>
        </template>

        <el-table :data="predictions" border style="width: 100%">
          <el-table-column prop="source_position_id" label="源阵位ID" width="120" v-if="isMultitaskResult"/>
          <el-table-column prop="event_type" label="事件类型" width="150" v-if="isMultitaskResult"/>
          <el-table-column prop="position_id" label="受影响阵位ID" width="120"/>
          <el-table-column prop="impact_probability" label="影响概率" width="120">
            <template #default="{row}">
              {{ (row.impact_probability * 100).toFixed(1) }}%
            </template>
          </el-table-column>
          <el-table-column prop="is_affected" label="是否受影响" width="120">
            <template #default="{row}">
              <el-tag :type="row.is_affected ? 'danger' : 'success'">
                {{ row.is_affected ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="predicted_impact_time_minutes" label="预计影响时间(分钟)"/>
        </el-table>
      </el-card>

      <el-card class="schedule-card" v-if="schedule.length > 0">
        <template #header>
          <div class="card-header">
            <span>调度方案</span>
          </div>
        </template>

        <el-table :data="schedule" border style="width: 100%">
          <el-table-column prop="task_id" label="任务ID" width="120"/>
          <el-table-column prop="position_id" label="分配阵位ID" width="120"/>
          <el-table-column prop="position_name" label="阵位名称"/>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { simulateEmergency, simulateMultitaskEmergency } from '@/api/emergency_fe.js'
import { parse } from 'papaparse'

export default {
  name: 'SimulEmerg',
  setup() {
    // 共用状态
    const formRef = ref(null)
    const submitting = ref(false)
    const submittingMultitask = ref(false)
    const showResults = ref(false)
    const showPositionsDialog = ref(false)
    const isMultitaskResult = ref(false)

    const positions = ref([])
    const currentPosition = ref(null)
    const predictions = ref([])
    const schedule = ref([])

    // 事件类型选项
    const eventTypes = [
      { value: 'guzhang_101', label: '设备故障' },
      { value: 'guzhang_102', label: '通信中断' },
      { value: 'guzhang_103', label: '人员缺勤' },
      { value: 'guzhang_104', label: '天气影响' },
      { value: 'guzhang_105', label: '电力中断' }
    ]

    // 单任务表单
    const form = reactive({
      event_type: '',
      position_id: '',
      severity: 0.5,
      duration: 30
    })

    // 多任务表单
    const multitaskForm = reactive({
      position_ids: [''],
      event_types: [''],
      severities: [0.5],
      durations: [30]
    })

    // 验证规则
    const positionRules = [
      { required: true, message: '请输入阵位ID', trigger: 'blur' },
      {
        validator: (rule, value, callback) => {
          if (!value) {
            callback(new Error('请输入阵位ID'))
            return
          }
          const isValid = positions.value.some(pos => pos.position_id === value)
          isValid ? callback() : callback(new Error('阵位ID不存在'))
        },
        trigger: 'blur'
      }
    ]

    const eventTypeRules = [
      { required: true, message: '请选择特情类型', trigger: 'blur' }
    ]

    const rules = {
      event_type: eventTypeRules,
      position_id: positionRules,
      severity: [{ required: true, message: '请设置严重程度', trigger: 'blur' }],
      duration: [{ required: true, message: '请设置持续时间', trigger: 'blur' }]
    }

    // 加载阵位数据
    const loadPositionsData = async () => {
      try {
        const response = await fetch(new URL('@/assets/positions.csv', import.meta.url).href)
        const csvData = await response.text()

        parse(csvData, {
          header: true,
          complete: (results) => {
            positions.value = results.data.map(item => ({
              position_id: item.position_id,
              position_type: item.position_type,
              type_identifier: item.type_identifier
            }))
          },
          error: (error) => {
            console.error('CSV解析错误:', error)
            ElMessage.error('阵位数据解析失败')
          }
        })
      } catch (error) {
        console.error('加载阵位数据失败:', error)
        ElMessage.error('加载阵位数据失败')
      }
    }

    // 阵位验证
    const validatePositionId = () => {
      if (!form.position_id) {
        currentPosition.value = null
        return
      }

      const found = positions.value.find(pos => pos.position_id === form.position_id)
      currentPosition.value = found || null
      if (!found) ElMessage.warning('输入的阵位ID不存在')
    }

    const validateMultitaskPositionId = (index) => {
      const positionId = multitaskForm.position_ids[index]
      if (!positionId) return

      const found = positions.value.some(pos => pos.position_id === positionId)
      if (!found) ElMessage.warning(`任务${index + 1}: 输入的阵位ID不存在`)
    }

    // 阵位选择相关
    const showPositionList = () => {
      showPositionsDialog.value = true
    }

    const selectPosition = (pos) => {
      if (isMultitaskResult.value) {
        // 如果是多任务结果，更新当前活动的输入框
        const activeIndex = multitaskForm.position_ids.length - 1
        multitaskForm.position_ids[activeIndex] = pos.position_id
      } else {
        form.position_id = pos.position_id
      }
      currentPosition.value = pos
      showPositionsDialog.value = false
    }

    // 任务管理
    const addTask = () => {
      multitaskForm.position_ids.push('')
      multitaskForm.event_types.push('')
      multitaskForm.severities.push(0.5)
      multitaskForm.durations.push(30)
    }

    const removeTask = (index) => {
      if (multitaskForm.position_ids.length > 1) {
        multitaskForm.position_ids.splice(index, 1)
        multitaskForm.event_types.splice(index, 1)
        multitaskForm.severities.splice(index, 1)
        multitaskForm.durations.splice(index, 1)
      }
    }

    // 表单提交
    const submitForm = async () => {
      try {
        await formRef.value.validate()
        submitting.value = true
        isMultitaskResult.value = false

        const res = await simulateEmergency({
          position_id: String(form.position_id),
          event_type: form.event_type,
          severity: form.severity,
          duration: form.duration
        })

        if (!Array.isArray(res)) {
          throw new Error('返回数据格式不正确，预期是数组')
        }

        predictions.value = res.map(item => ({
          position_id: String(item.position_id),
          impact_probability: Number(item.impact_probability),
          is_affected: Boolean(item.is_affected),
          predicted_impact_time_minutes: Number(item.predicted_impact_time_minutes)
        }))

        schedule.value = []
        showResults.value = true
        ElMessage.success('模拟成功')
      } catch (error) {
        console.error('模拟失败详情:', error)
        ElMessage.error(error.response?.data?.message || error.message || '模拟失败')
      } finally {
        submitting.value = false
      }
    }

    const submitMultitaskForm = async () => {
      try {
        // 验证所有必填字段
        const hasEmptyFields = multitaskForm.position_ids.some((id, index) =>
          !id || !multitaskForm.event_types[index]
        )

        if (hasEmptyFields) {
          throw new Error('请填写所有任务的必填字段')
        }

        // 验证所有阵位ID
        const invalidPositions = multitaskForm.position_ids.filter(id =>
          !positions.value.some(pos => pos.position_id === id)
        )

        if (invalidPositions.length > 0) {
          throw new Error(`以下阵位ID不存在: ${invalidPositions.join(', ')}`)
        }

        submittingMultitask.value = true
        isMultitaskResult.value = true

        const res = await simulateMultitaskEmergency({
          position_ids: multitaskForm.position_ids.map(String),
          event_types: multitaskForm.event_types,
          severities: multitaskForm.severities,
          durations: multitaskForm.durations
        })

        // 处理多任务返回结果
        predictions.value = res.flatMap(prediction =>
          prediction.affected_positions.map(affected => ({
            source_position_id: prediction.source_position_id,
            event_type: prediction.event_type,
            position_id: affected.position_id,
            impact_probability: affected.impact_probability,
            is_affected: affected.is_affected,
            predicted_impact_time_minutes: affected.predicted_impact_time_minutes
          }))
        )

        schedule.value = []
        showResults.value = true
        ElMessage.success('多任务模拟成功')
      } catch (error) {
        console.error('多任务模拟失败:', error)
        ElMessage.error(error.response?.data?.message || error.message || '多任务模拟失败')
      } finally {
        submittingMultitask.value = false
      }
    }

    // 重置表单
    const resetForm = () => {
      formRef.value.resetFields()
      showResults.value = false
      predictions.value = []
      schedule.value = []
      currentPosition.value = null
      isMultitaskResult.value = false
    }

    onMounted(() => {
      loadPositionsData()
    })

    return {
      formRef,
      form,
      multitaskForm,
      rules,
      positionRules,
      eventTypeRules,
      submitting,
      submittingMultitask,
      eventTypes,
      positions,
      currentPosition,
      showPositionList,
      validatePositionId,
      validateMultitaskPositionId,
      showPositionsDialog,
      selectPosition,
      addTask,
      removeTask,
      submitForm,
      submitMultitaskForm,
      resetForm,
      predictions,
      schedule,
      showResults,
      isMultitaskResult
    }
  }
}
</script>

<style scoped>
.simulation-container {
  padding: 20px;
}

.form-card {
  margin-bottom: 20px;
}

.result-section {
  margin-top: 20px;
}

.result-card, .schedule-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}

.position-info {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.task-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 15px;
  background-color: #f5f7fa;
  position: relative;
}

.task-item:last-child {
  margin-bottom: 0;
}
</style>