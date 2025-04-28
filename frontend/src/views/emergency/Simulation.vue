<template>
  <div>
    <h1>突发事件影响预测与调度</h1>
    <form @submit.prevent="submitPrediction">
      <div>
        <label for="position_id">故障阵位ID:</label>
        <input type="number" id="position_id" v-model.number="position_id" required />
      </div>
      <div>
        <label for="event_type">事件类型:</label>
        <input type="text" id="event_type" v-model="event_type" required />
      </div>
      <div>
        <label for="severity">严重性 (0-1):</label>
        <input type="number" id="severity" v-model.number="severity" step="0.01" required />
      </div>
      <div>
        <label for="duration">持续时间 (分钟):</label>
        <input type="number" id="duration" v-model.number="duration" required />
      </div>
      <button type="submit">提交</button>
    </form>

    <div v-if="predictions.length > 0">
      <h2>预测结果</h2>
      <table>
        <thead>
          <tr>
            <th>阵位ID</th>
            <th>影响概率</th>
            <th>预计影响时间 (分钟)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pred in predictions" :key="pred.position_id">
            <td>{{ pred.position_id }}</td>
            <td>{{ pred.impact_probability.toFixed(4) }}</td>
            <td>{{ pred.predicted_impact_time_minutes.toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="schedule.length > 0">
      <h2>调度结果</h2>
      <table>
        <thead>
          <tr>
            <th>任务ID</th>
            <th>原阵位ID</th>
            <th>新阵位ID</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in schedule" :key="item.task_id">
            <td>{{ item.task_id }}</td>
            <td>{{ item.original_position }}</td>
            <td>{{ item.new_position }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'

export default {
  data() {
    return {
      position_id: null,
      event_type: '',
      severity: null,
      duration: null,
      predictions: [],
      schedule: []
    };
  },
  methods: {
    async submitPrediction() {
      try {
        const response = await axios.post('/app/predict', {
          position_id: this.position_id,
          event_type: this.event_type,
          severity: this.severity,
          duration: this.duration
        });
        this.predictions = response.data;

        // 调用调度接口
        const scheduleResponse = await axios.post('/app/schedule', {
          position_id: this.position_id,
          event_type: this.event_type,
          severity: this.severity,
          duration: this.duration
        });
        this.schedule = scheduleResponse.data.schedule;
      } catch (error) {
        console.error('预测或调度失败:', error);
        alert('预测或调度失败，请检查输入参数');
      }
    }
  }
};
</script>