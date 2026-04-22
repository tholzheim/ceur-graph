import { apiFetch } from '../api.js'
import { getLabel } from '../labelCache.js'

export default {
  name: 'ItemSearchInput',
  props: {
    modelValue: { type: String, default: '' },
    placeholder: { type: String, default: 'Search or enter QID…' },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const { ref, watch } = Vue

    const text = ref(props.modelValue || '')
    const suggestions = ref([])
    const activeIdx = ref(-1)
    const resolvedLabel = ref('')
    const searchError = ref('')
    const inputEl = ref(null)
    const dropdownStyle = ref({})
    let debounceTimer = null

    watch(suggestions, val => {
      if (val.length && inputEl.value) {
        const rect = inputEl.value.getBoundingClientRect()
        dropdownStyle.value = {
          position: 'fixed',
          top: rect.bottom + 'px',
          left: rect.left + 'px',
          width: rect.width + 'px',
          zIndex: 9999,
          background: 'var(--card-background-color)',
          border: '1px solid var(--muted-border-color)',
          borderRadius: 'var(--border-radius)',
          maxHeight: '240px',
          overflowY: 'auto',
        }
      }
    })

    async function fetchLabel(qid) {
      resolvedLabel.value = await getLabel(qid)
    }

    watch(() => props.modelValue, v => {
      if (v !== text.value) {
        text.value = v || ''
        resolvedLabel.value = ''
        if (v && /^Q\d+$/i.test(v)) fetchLabel(v)
      }
    })

    // Resolve label on mount if initial value is a QID
    if (props.modelValue && /^Q\d+$/i.test(props.modelValue)) {
      fetchLabel(props.modelValue)
    }

    async function onInput() {
      activeIdx.value = -1
      clearTimeout(debounceTimer)
      searchError.value = ''
      resolvedLabel.value = ''
      const q = text.value.trim()
      if (!q) { suggestions.value = []; return }
      if (q.match(/^Q\d+$/i)) {
        suggestions.value = []
        fetchLabel(q)
        return
      }
      debounceTimer = setTimeout(async () => {
        try {
          suggestions.value = await apiFetch(`/api/entity-search?q=${encodeURIComponent(q)}&limit=8`) || []
          searchError.value = ''
        } catch (e) {
          suggestions.value = []
          searchError.value = e.message || 'Search failed'
        }
      }, 300)
    }

    function select(item) {
      text.value = item.id
      resolvedLabel.value = item.label || ''
      suggestions.value = []
      emit('update:modelValue', item.id)
    }

    function onBlur() {
      setTimeout(() => { suggestions.value = [] }, 150)
      emit('update:modelValue', text.value.trim())
    }

    function onKey(e) {
      if (!suggestions.value.length) return
      if (e.key === 'ArrowDown') { activeIdx.value = Math.min(activeIdx.value + 1, suggestions.value.length - 1); e.preventDefault() }
      else if (e.key === 'ArrowUp') { activeIdx.value = Math.max(activeIdx.value - 1, 0); e.preventDefault() }
      else if (e.key === 'Enter' && activeIdx.value >= 0) { select(suggestions.value[activeIdx.value]); e.preventDefault() }
      else if (e.key === 'Escape') { suggestions.value = [] }
    }

    return { text, suggestions, activeIdx, resolvedLabel, searchError, inputEl, dropdownStyle, onInput, select, onBlur, onKey }
  },
  template: `
    <div class="search-wrap">
      <input
        ref="inputEl"
        v-model="text"
        type="text"
        :placeholder="placeholder"
        @input="onInput"
        @blur="onBlur"
        @keydown="onKey"
        autocomplete="off"
        style="margin:0"
      />
      <teleport to="body">
        <div v-if="suggestions.length" :style="dropdownStyle">
          <div
            v-for="(s, i) in suggestions"
            :key="s.id"
            class="suggestion-item"
            :class="{ active: i === activeIdx }"
            @mousedown.prevent="select(s)"
          >
            <span class="suggestion-label">{{ s.label }}</span>
            <span class="suggestion-id">({{ s.id }})</span>
            <br><span class="suggestion-desc">{{ s.description }}</span>
          </div>
        </div>
      </teleport>
      <small v-if="resolvedLabel" style="color:var(--muted-color)">{{ resolvedLabel }}</small>
      <small v-if="searchError" style="color:var(--del-color)">{{ searchError }}</small>
    </div>
  `
}
