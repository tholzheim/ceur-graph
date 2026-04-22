import { apiPost, apiPut } from '../api.js'

export default {
  name: 'CommitDialog',
  props: {
    open: { type: Boolean, default: false },
    pendingData: { type: Object, required: true },
    loadedData: { type: Object, default: null },
    isNew: { type: Boolean, default: false },
    entityConfig: { type: Object, required: true },
  },
  emits: ['close', 'saved'],
  setup(props, { emit }) {
    const { computed, ref } = Vue

    const loading = ref(false)
    const error = ref('')

    const changedFields = computed(() => {
      const fields = []
      for (const [k, v] of Object.entries(props.pendingData)) {
        if (v == null || v === '' || (Array.isArray(v) && !v.length)) continue
        const oldVal = props.loadedData?.[k]
        const newStr = Array.isArray(v) ? v.join(', ') : String(v)
        const oldStr = oldVal != null ? (Array.isArray(oldVal) ? oldVal.join(', ') : String(oldVal)) : null
        if (newStr !== oldStr) {
          fields.push({ name: k, label: k.replace(/_/g, ' '), oldVal: oldStr, newVal: newStr })
        }
      }
      return fields
    })

    function close() {
      error.value = ''
      emit('close')
    }

    async function confirm() {
      loading.value = true
      error.value = ''
      try {
        const prefix = props.entityConfig.endpoint_prefix
        const body = {}
        for (const [k, v] of Object.entries(props.pendingData)) {
          if (v !== null && v !== undefined) body[k] = v
        }
        let result
        if (props.isNew) {
          result = await apiPost(`${prefix}/`, body)
        } else {
          const qid = props.loadedData?.qid
          result = await apiPut(`${prefix}/${qid}`, body)
        }
        emit('saved', result)
        close()
      } catch (e) {
        error.value = e.message
      } finally {
        loading.value = false
      }
    }

    return { changedFields, loading, error, close, confirm }
  },
  template: `
    <dialog :open="open">
      <article>
        <header>
          <button rel="prev" @click="close"></button>
          <strong>{{ isNew ? 'Create' : 'Update' }} {{ entityConfig.name }}</strong>
        </header>

        <div v-if="error" class="error-banner">{{ error }}</div>

        <p v-if="!changedFields.length"><em>No changes detected.</em></p>
        <template v-else>
          <p>Review changes before writing to Wikibase:</p>
          <table class="diff-table">
            <thead><tr><th>Field</th><th v-if="!isNew">Current</th><th>New Value</th></tr></thead>
            <tbody>
              <tr v-for="f in changedFields" :key="f.name">
                <td>{{ f.label }}</td>
                <td v-if="!isNew" style="color:var(--muted-color)">{{ f.oldVal ?? '—' }}</td>
                <td><strong>{{ f.newVal }}</strong></td>
              </tr>
            </tbody>
          </table>
        </template>

        <footer>
          <button class="secondary outline" @click="close">Cancel</button>
          <button @click="confirm" :aria-busy="loading" :disabled="!changedFields.length">
            Confirm &amp; Write to Wikibase
          </button>
        </footer>
      </article>
    </dialog>
  `
}
