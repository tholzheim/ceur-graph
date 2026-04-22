import ItemSearchInput from './ItemSearchInput.js'

export default {
  name: 'FieldInput',
  components: { ItemSearchInput },
  props: {
    field: { type: Object, required: true },
    modelValue: { default: null },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const { computed } = Vue

    const isItem = computed(() => props.field.wikibase_type === 'wikibase-item')
    const isNumber = computed(() => props.field.wikibase_type === 'quantity')
    const isUrl = computed(() => props.field.wikibase_type === 'url')
    const isList = computed(() => props.field.field_type === 'list')

    const inputType = computed(() => {
      if (isNumber.value) return 'number'
      if (isUrl.value) return 'url'
      return 'text'
    })

    const listVal = computed(() => {
      if (!isList.value) return []
      return Array.isArray(props.modelValue) ? props.modelValue : (props.modelValue ? [props.modelValue] : [''])
    })

    function updateList(idx, newVal) {
      const arr = [...listVal.value]
      arr[idx] = newVal
      emit('update:modelValue', arr)
    }

    function addListItem() {
      emit('update:modelValue', [...listVal.value, ''])
    }

    function removeListItem(idx) {
      const arr = listVal.value.filter((_, i) => i !== idx)
      emit('update:modelValue', arr.length ? arr : [''])
    }

    function onSingle(e) {
      const v = e.target ? e.target.value : e
      emit('update:modelValue', isNumber.value ? (v === '' ? null : Number(v)) : v)
    }

    return { isItem, isNumber, isUrl, isList, inputType, listVal, updateList, addListItem, removeListItem, onSingle }
  },
  template: `
    <div>
      <!-- List field -->
      <template v-if="isList">
        <div v-for="(val, idx) in listVal" :key="idx" class="list-field-item">
          <item-search-input
            v-if="isItem"
            :model-value="val"
            @update:model-value="updateList(idx, $event)"
          />
          <input
            v-else
            :type="inputType"
            :value="val"
            @input="updateList(idx, $event.target.value)"
            style="margin:0"
          />
          <button class="outline" style="padding:0.3rem 0.6rem;margin:0" @click.prevent="removeListItem(idx)">✕</button>
        </div>
        <button class="secondary outline" style="padding:0.3rem 0.75rem" @click.prevent="addListItem">+ Add</button>
      </template>

      <!-- Single item field -->
      <item-search-input
        v-else-if="isItem"
        :model-value="modelValue || ''"
        @update:model-value="$emit('update:modelValue', $event)"
      />

      <!-- Single scalar field -->
      <input
        v-else
        :type="inputType"
        :value="modelValue ?? ''"
        @input="onSingle"
        style="margin:0"
      />
    </div>
  `
}
