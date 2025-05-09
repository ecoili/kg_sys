<template>
  <div class="simulation-container">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span>特情模拟</span>
        </div>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="特情类型" prop="event_type">
          <el-select v-model="form.event_type" placeholder="请选择特情类型">
            <el-option
              v-for="item in eventTypes"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="阵位ID" prop="position_id">
          <el-input
            v-model="form.position_id"
            placeholder="请输入阵位ID"
            @blur="validatePositionId">
            <template #append>
              <el-button @click="showPositionList">查看所有阵位</el-button>
            </template>
          </el-input>
<!--          <div class="position-info" v-if="currentPosition">-->
<!--            {{ currentPosition.type_identifier }} ({{ currentPosition.position_type }})-->
<!--          </div>-->
        </el-form-item>

        <el-form-item label="严重程度" prop="severity">
          <el-slider
            v-model="form.severity"
            :min="0"
            :max="1"
            :step="0.01"
            show-input>
          </el-slider>
        </el-form-item>

        <el-form-item label="持续时间(分钟)" prop="duration">
          <el-input-number
            v-model="form.duration"
            :min="5"
            :max="240"
            :step="5">
          </el-input-number>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="submitForm"
            :loading="submitting">
            提交模拟
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
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

<!--        <el-table :data="predictions" border style="width: 100%">-->
<!--          <el-table-column prop="position_id" label="阵位ID" width="120"/>-->
<!--          <el-table-column prop="impact_probability" label="影响概率" width="120">-->
<!--            <template #default="{row}">-->
<!--              {{ (row.impact_probability * 100).toFixed(1) }}%-->
<!--            </template>-->
<!--          </el-table-column>-->
<!--          <el-table-column prop="is_affected" label="是否受影响" width="120">-->
<!--            <template #default="{row}">-->
<!--              <el-tag :type="row.is_affected ? 'danger' : 'success'">-->
<!--                {{ row.is_affected ? '是' : '否' }}-->
<!--              </el-tag>-->
<!--            </template>-->
<!--          </el-table-column>-->
<!--          <el-table-column prop="predicted_impact_time_minutes" label="预计影响时间(分钟)"/>-->
<!--        </el-table>-->
        <!-- 预测结果表格 -->
            <el-table :data="predictions" border style="width: 100%">
  <el-table-column prop="position_id" label="阵位ID" width="200">
    <template #default="{row}">
      <div>{{ row.position_id }}</div>
    </template>
  </el-table-column>

  <el-table-column prop="position_name" label="阵位名称" width="200">
    <template #default="{row}">
      <div>{{ row.position_name || '未知' }}</div>
    </template>
  </el-table-column>

  <el-table-column prop="impact_probability" label="影响概率" width="200">
    <template #default="{row}">
      {{ (row.impact_probability * 100).toFixed(1) }}%
    </template>
  </el-table-column>
  <el-table-column prop="is_affected" label="是否受影响(概率>50%)" width="200">
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

<!--        <el-table :data="schedule" border style="width: 100%">-->
<!--          <el-table-column prop="task_id" label="任务ID" width="120"/>-->
<!--          <el-table-column prop="original_position_name" label="原阵位"/>-->
<!--          <el-table-column prop="position_name" label="新阵位"/>-->
<!--          <el-table-column prop="reason" label="调度原因"/>-->
<!--          <el-table-column prop="distance" label="距离(米)" width="120"/>-->
<!--          <el-table-column prop="move_time" label="预计移动时间(分钟)" width="150"/>-->
<!--        </el-table>-->
        <!-- 调度方案表格 -->
            <el-table :data="schedule" border style="width: 100%">
                <el-table-column prop="task_id" label="任务" width="180">
                  <template #default="{row}">
                    <div>ID: {{ row.task_id }}</div>
                    <div>名称: {{ row.task_name }}</div>
                  </template>
                </el-table-column>

              <el-table-column prop="priority" label="任务优先级"/>

                <el-table-column prop="original_position" label="原阵位" width="180">
                  <template #default="{row}">
                    <div>ID: {{ row.original_position }}</div>
                    <div>名称: {{ row.original_position_name }}</div>
                  </template>
                </el-table-column>
                <el-table-column prop="new_position" label="新阵位" width="180">
                  <template #default="{row}">
                    <div>ID: {{ row.new_position }}</div>
                    <div>名称: {{ row.new_position_name }}</div>
                  </template>
                </el-table-column>
                <el-table-column prop="reason" label="调度原因"/>
                <el-table-column prop="distance" label="移动距离(米)" width="120"/>
                <el-table-column prop="move_time" label="预计处理时间(分钟)" width="150"/>
              </el-table>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import {simulateEmergency, simulateEmergency2, simulateEmergency3} from '@/api/emergency_fe.js'
import { parse } from 'papaparse'

export default {
  name: 'SimulEmerg',
  setup() {
    const formRef = ref(null)
    const submitting = ref(false)
    const showResults = ref(false)
    const showPositionsDialog = ref(false)

    const form = reactive({
      event_type: '',
      position_id: '',
      severity: 0.5,
      duration: 30
    })

    const positions = ref([])
    const currentPosition = ref(null)
    const predictions = ref([])
    const schedule = ref([])

    const eventTypes = [
      { value: 'guzhang_101', label: '设备故障' },
      { value: 'guzhang_102', label: '通信中断' },
      { value: 'guzhang_103', label: '人员缺勤' },
      { value: 'guzhang_104', label: '天气影响' },
      { value: 'guzhang_105', label: '电力中断' }
    ]

    const rules = {
      event_type: [{ required: true, message: '请选择特情类型', trigger: 'blur' }],
      position_id: [
        { required: true, message: '请输入阵位ID', trigger: 'blur' },
        {
          validator: (rule, value, callback) => {
            if (!value) {
              callback(new Error('请输入阵位ID'))
              return
            }
            const isValid = positions.value.some(
              pos => pos.position_id === value
            )
            isValid ? callback() : callback(new Error('阵位ID不存在'))
          },
          trigger: 'blur'
        }
      ],
      severity: [{ required: true, message: '请设置严重程度', trigger: 'blur' }],
      duration: [{ required: true, message: '请设置持续时间', trigger: 'blur' }]
    }

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

    const validatePositionId = () => {
      if (!form.position_id) {
        currentPosition.value = null
        return
      }

      const found = positions.value.find(
        pos => pos.position_id === form.position_id
      )

      if (found) {
        currentPosition.value = found
      } else {
        currentPosition.value = null
        ElMessage.warning('输入的阵位ID不存在')
      }
    }

    const showPositionList = () => {
      showPositionsDialog.value = true
    }

    const selectPosition = (pos) => {
      form.position_id = pos.position_id
      currentPosition.value = pos
      showPositionsDialog.value = false
    }

//     const submitForm = async () => {
//   try {
//     await formRef.value.validate()
//     submitting.value = true
//
//     const response = await simulateEmergency3({
//       position_id: String(form.position_id),
//       event_type: form.event_type,
//       severity: form.severity,
//       duration: form.duration
//     })
//
//     // 正确的响应结构应该是 response 直接包含后端返回的数据
//     console.log("完整API响应", response)
//
//     // 确保响应包含必要字段
//     if (!response || !response.predictions) {
//       throw new Error('返回数据格式不正确')
//     }
//
//     // 处理预测结果
//     predictions.value = Array.isArray(response.predictions)
//       ? response.predictions.map(item => ({
//           position_id: String(item.position_id),
//           impact_probability: Number(item.impact_probability),
//           is_affected: Boolean(item.is_affected),
//           predicted_impact_time_minutes: Number(item.predicted_impact_time_minutes)
//         }))
//       : []
//
//     // 处理调度结果
//     schedule.value = Array.isArray(response.schedule)
//       ? response.schedule.map(item => ({
//           task_id: String(item.task_id),
//           original_position_name: item.original_position_name,
//           position_name: item.position_name,
//           reason: item.reason,
//           distance: item.distance,
//           move_time: item.move_time
//         }))
//       : []
//
//     showResults.value = true
//     ElMessage.success('模拟成功')
//
//   } catch (error) {
//     const detailedError = {
//       message: error.message,
//       response: error.response,
//       stack: error.stack
//     }
//     console.error('完整错误详情:', detailedError)
//     ElMessage.error(`模拟失败: ${error.message}`)
//     } finally {
//     submitting.value = false
//   }
// }
    const isMounted = ref(true)

    onBeforeUnmount(() => {
      isMounted.value = false
    })
    const submitForm = async () => {
  try {
    if (!isMounted.value) return
    await formRef.value.validate()
    submitting.value = true

    const response = await simulateEmergency3({
      position_id: String(form.position_id),
      event_type: form.event_type,
      severity: form.severity,
      duration: form.duration
    })

    // 检查组件是否仍然挂载
    if (!formRef.value) return

    console.log("完整API响应", response)

    if (!response || !response.predictions) {
      throw new Error('返回数据格式不正确')
    }

    // 处理预测结果
    predictions.value = Array.isArray(response.predictions)
      ? response.predictions.map(item => ({
          position_id: String(item.position_id),
          position_name: item.position_name || '未知',
          impact_probability: Number(item.impact_probability),
          is_affected: Boolean(item.is_affected),
          predicted_impact_time_minutes: Number(item.predicted_impact_time_minutes)
        }))
      : []

    // 处理调度结果
    schedule.value = Array.isArray(response.schedule)
      ? response.schedule.map(item => ({
          task_id: String(item.task_id),
          task_type: item.task_type || '未知',
          task_name: item.task_name || '未知',
          original_position: String(item.original_position),
          original_position_name: item.original_position_name || '未知',
          new_position: String(item.new_position),
          new_position_name: item.new_position_name || '未知',
          reason: item.reason,
          priority: item.priority,
          // distance: item.distance,
          // move_time: item.move_time
          distance: Math.round(Number(item.distance)), // 四舍五入为整数
          move_time: Math.round(Number(item.move_time)) // 四舍五入为整数
        }))
      : []

    showResults.value = true
    ElMessage.success('模拟成功')

  } catch (error) {
    if (!isMounted.value) return
    const detailedError = {
      message: error.message,
      response: error.response,
      stack: error.stack
    }
    console.error('完整错误详情:', detailedError)
    ElMessage.error(`模拟失败: ${error.message}`)
  } finally {
    if (!isMounted.value) return
    submitting.value = false
  }
}

    const resetForm = () => {
      formRef.value.resetFields()
      showResults.value = false
      predictions.value = []
      schedule.value = []
      currentPosition.value = null
    }

    onMounted(() => {
      loadPositionsData()
    })

    return {
      formRef,
      form,
      rules,
      submitting,
      eventTypes,
      positions,
      currentPosition,
      showPositionList,
      validatePositionId,
      showPositionsDialog,
      selectPosition,
      submitForm,
      resetForm,
      predictions,
      schedule,
      showResults
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
</style>