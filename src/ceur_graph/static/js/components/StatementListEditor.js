import { apiFetch, apiPost, apiPut, apiDelete } from '../api.js'
import FieldInput from './FieldInput.js'
import { getLabel } from '../labelCache.js'

export default {
  name: 'StatementListEditor',
  components: { FieldInput },
  props: {
    field: { type: Object, required: true },  // statement_list field config
    parentQid: { type: String, default: null },
  },
  setup(props) {
    const { ref, reactive, watch, computed } = Vue

    const rows = ref([])
    const loading = ref(false)
    const error = ref('')
    const success = ref('')
    const labelMap = reactive({})

    // Dialog state
    const dialogOpen = ref(false)
    const editingRow = ref(null)       // null = new, else existing row object
    const formData = reactive({})
    const dialogError = ref('')
    const dialogLoading = ref(false)
    const deleteConfirm = ref(null)    // row being confirmed for delete

    function endpointFor(parentQid) {
      if (!props.field.statement_endpoint || !parentQid) return null
      return props.field.statement_endpoint.replace(/\{[^}]+\}/, parentQid)
    }

    function resolveRowLabels() {
      const itemFields = props.field.statement_fields.filter(f => f.wikibase_type === 'item')
      for (const row of rows.value) {
        for (const f of itemFields) {
          const qid = row[f.name]
          if (qid && !(qid in labelMap)) {
            getLabel(qid).then(label => { if (label) labelMap[qid] = label })
          }
        }
      }
    }

    async function load() {
      const url = endpointFor(props.parentQid)
      if (!url) return
      loading.value = true
      error.value = ''
      try {
        rows.value = await apiFetch(url) || []
        resolveRowLabels()
      } catch (e) {
        error.value = e.message
      } finally {
        loading.value = false
      }
    }

    watch(() => props.parentQid, load, { immediate: true })

    function openNew() {
      editingRow.value = null
      Object.keys(formData).forEach(k => delete formData[k])
      props.field.statement_fields.forEach(f => {
        formData[f.name] = f.field_type === 'list' ? [] : ''
      })
      dialogError.value = ''
      dialogOpen.value = true
    }

    function openEdit(row) {
      editingRow.value = row
      Object.keys(formData).forEach(k => delete formData[k])
      props.field.statement_fields.forEach(f => {
        formData[f.name] = row[f.name] ?? (f.field_type === 'list' ? [] : '')
      })
      dialogError.value = ''
      dialogOpen.value = true
    }

    function closeDialog() {
      dialogOpen.value = false
    }

    async function saveDialog() {
      const url = endpointFor(props.parentQid)
      if (!url) return
      dialogLoading.value = true
      dialogError.value = ''
      try {
        const body = { ...formData }
        // Clean up empty list items
        props.field.statement_fields.forEach(f => {
          if (f.field_type === 'list' && Array.isArray(body[f.name])) {
            body[f.name] = body[f.name].filter(v => v !== '' && v != null)
          }
        })
        if (editingRow.value) {
          const stmtId = editingRow.value.statement_id
          await apiPut(`${url}/${stmtId}`, body)
        } else {
          await apiPost(`${url}/`, body)
        }
        success.value = editingRow.value ? 'Statement updated.' : 'Statement added.'
        setTimeout(() => { success.value = '' }, 3000)
        dialogOpen.value = false
        await load()
      } catch (e) {
        dialogError.value = e.message
      } finally {
        dialogLoading.value = false
      }
    }

    async function deleteRow(row) {
      const url = endpointFor(props.parentQid)
      if (!url) return
      try {
        await apiDelete(`${url}/${row.statement_id}`)
        success.value = 'Statement removed.'
        setTimeout(() => { success.value = '' }, 3000)
        deleteConfirm.value = null
        await load()
      } catch (e) {
        error.value = e.message
      }
    }

    function displayValue(row, f) {
      const v = row[f.name]
      if (v == null || v === '') return '—'
      if (Array.isArray(v)) return v.join(', ') || '—'
      if (f.wikibase_type === 'item') return labelMap[v] ? `${labelMap[v]} (${v})` : v
      return String(v)
    }

    const visibleCols = computed(() =>
      props.field.statement_fields.filter(f => f.name !== 'object_named_as')
    )

    return {
      rows, loading, error, success, labelMap,
      dialogOpen, editingRow, formData, dialogError, dialogLoading, deleteConfirm,
      openNew, openEdit, closeDialog, saveDialog, deleteRow, displayValue, visibleCols,
    }
  },
  template: `
    <div>
      <div v-if="success" class="success-banner">{{ success }}</div>
      <div v-if="error" class="error-banner">{{ error }}</div>

      <div v-if="loading">
        <span class="spinner"></span> Loading…
      </div>

      <table v-else-if="rows.length" class="stmt-table">
        <thead>
          <tr>
            <th v-for="f in visibleCols" :key="f.name">{{ f.label }}</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.statement_id">
            <td v-for="f in visibleCols" :key="f.name">{{ displayValue(row, f) }}</td>
            <td>
              <button class="outline" style="padding:0.2rem 0.6rem;margin:0 0.25rem 0 0" @click="openEdit(row)">Edit</button>
              <template v-if="deleteConfirm === row">
                <small>Sure? </small>
                <button style="padding:0.2rem 0.5rem;margin:0 0.25rem 0 0" @click="deleteRow(row)">Yes</button>
                <button class="secondary outline" style="padding:0.2rem 0.5rem;margin:0" @click="deleteConfirm=null">No</button>
              </template>
              <button v-else class="secondary outline" style="padding:0.2rem 0.6rem;margin:0" @click="deleteConfirm=row">Remove</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else><em>No entries yet.</em></p>

      <button class="outline" style="margin-top:0.5rem" @click="openNew" :disabled="!parentQid">+ Add {{ field.label }}</button>
      <small v-if="!parentQid" style="margin-left:0.5rem;color:var(--muted-color)">Save the entity first to add statements</small>

      <!-- Dialog -->
      <dialog :open="dialogOpen">
        <article>
          <header>
            <button rel="prev" @click="closeDialog"></button>
            <strong>{{ editingRow ? 'Edit' : 'Add' }} {{ field.label }}</strong>
          </header>
          <div v-if="dialogError" class="error-banner">{{ dialogError }}</div>
          <form @submit.prevent="saveDialog">
            <div v-for="f in field.statement_fields" :key="f.name" class="field-row">
              <label>
                {{ f.label }}<span v-if="f.required" style="color:red">*</span>
                <field-input :field="f" v-model="formData[f.name]" />
              </label>
            </div>
            <footer>
              <button class="secondary outline" type="button" @click="closeDialog">Cancel</button>
              <button type="submit" :aria-busy="dialogLoading">Save</button>
            </footer>
          </form>
        </article>
      </dialog>
    </div>
  `
}
