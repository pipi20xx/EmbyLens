<template>
  <n-modal
    :show="show"
    @update:show="$emit('update:show', $event)"
    preset="card"
    :title="isNew ? '添加新规则' : '编辑规则'"
    style="width: 650px"
    :bordered="false"
  >
    <n-form label-placement="left" label-width="120" size="medium">
      <n-form-item label="规则名称:">
        <n-input v-model:value="editingRule.name" placeholder="起个名字方便识别" />
      </n-form-item>
      
      <n-form-item label="生成的标签:">
        <n-input v-model:value="editingRule.tag" placeholder="Emby 中将要显示的标签名" />
      </n-form-item>

      <n-form-item label="国家/地区:">
        <n-select
          multiple filterable tag
          v-model:value="editingRule.conditions.countries"
          :options="countryOptions"
          placeholder="满足其中任一国家即可"
        />
      </n-form-item>

      <n-form-item label="流派类型:">
        <n-select
          multiple filterable tag
          v-model:value="editingRule.conditions.genres"
          :options="genreOptions"
          placeholder="满足其中任一流派即可"
        />
      </n-form-item>

      <n-form-item label="作用于年份:">
        <n-input 
          v-model:value="editingRule.conditions.years_text" 
          placeholder="例如: 2020, 2022 2024 或 1999-2020" 
        />
      </n-form-item>

      <n-form-item label="作用对象:">
        <n-radio-group v-model:value="editingRule.item_type">
          <n-space>
            <n-radio value="all">全部</n-radio>
            <n-radio value="movie">仅电影</n-radio>
            <n-radio value="series">仅剧集</n-radio>
          </n-space>
        </n-radio-group>
      </n-form-item>

      <n-form-item label="匹配模式:">
        <n-space vertical>
          <n-checkbox v-model:checked="editingRule.match_all_conditions">
            严格匹配所有条件 (国家/地区和类型必须全部命中)
          </n-checkbox>
          <n-checkbox v-model:checked="editingRule.is_negative_match">
            负向匹配 (满足条件的项目将被排除，不满足才生效)
          </n-checkbox>
        </n-space>
      </n-form-item>
    </n-form>

    <template #footer>
      <n-space justify="end">
        <n-button @click="$emit('update:show', false)">取消</n-button>
        <n-button type="primary" @click="handleConfirm">保存规则</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { 
  NModal, NForm, NFormItem, NInput, NSelect, NButton, NSpace, 
  NRadioGroup, NRadio, NCheckbox 
} from 'naive-ui'

const props = defineProps<{ 
  show: boolean, 
  rule: any,
  isNew: boolean
}>()

const emit = defineEmits(['update:show', 'confirm'])

const editingRule = ref<any>({
  name: '', tag: '', item_type: 'all', match_all_conditions: false, is_negative_match: false,
  conditions: { countries: [], genres: [], years_text: '' }
})

const countryOptions = [
  "爱尔兰", "澳大利亚", "巴西", "比利时", "波兰", "丹麦", "德国", "俄罗斯", "法国", 
  "韩国", "荷兰", "加拿大", "美国", "墨西哥", "挪威", "日本", "瑞典", "沙特阿拉伯", 
  "泰国", "西班牙", "意大利", "印度", "英国", "中国澳门", "中国大陆", "中国台湾", "中国香港"
].map(c => ({ label: c, value: c }))

const genreOptions = [
  "爱情", "电视电影", "动画", "动作", "动作冒险", "儿童", "犯罪", "肥皂剧", "纪录片", 
  "家庭", "惊悚", "剧情", "科幻", "科幻奇幻", "恐怖", "历史", "冒险", "奇幻", 
  "脱口秀", "西部", "喜剧", "新闻", "悬疑", "音乐", "战争", "战争政治", "真人秀"
].map(g => ({ label: g, value: g }))

watch(() => props.show, (val) => {
  if (val) {
    editingRule.value = JSON.parse(JSON.stringify(props.rule))
  }
})

const handleConfirm = () => {
  emit('confirm', editingRule.value)
}
</script>