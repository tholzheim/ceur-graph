import { apiFetch } from '../api.js'
import FieldInput from './FieldInput.js'
import { getLabel } from '../labelCache.js'

let _nextId = 0

export default {
  name: 'StatementListEditor',
  components: { FieldInput },
  emits: ['update:pending'],
  props: {
    field: { type: Object, required: true },
    parentQid: { type: String, default: null },
    clearSignal: { type: Number, default: 0 },
  },
  setup(props, { emit }) {
    const { ref, reactive, watch, computed } = Vue

    const rows = ref([])
    const loading = ref(false)
    const error = ref('')
    const labelMap = reactive({})

    const pendingOps = ref([])

    // Dialog state
    const dialogOpen = ref(false)
    const editingRow = ref(null)
    const formData = reactive({})
    const dialogError = ref('')
    const deleteConfirm = ref(null)

    // --- Derived pending state ---
    const pendingDeleteIds = computed(() =>
      new Set(pendingOps.value.filter(op => op.type === 'delete').map(op => op.statementId))
    )
    const pendingEditMap = computed(() =>
      Object.fromEntries(pendingOps.value.filter(op => op.type === 'edit').map(op => [op.statementId, op]))
    )
    const pendingAdds = computed(() => pendingOps.value.filter(op => op.type === 'add'))

    // --- Label resolution ---
    function resolveLabelsForRow(row) {
      const itemFields = props.field.statement_fields.filter(f => f.wikibase_type === 'item')
      for (const f of itemFields) {
        const qid = row[f.name]
        if (qid && !(qid in labelMap)) {
          getLabel(qid).then(label => { if (label) labelMap[qid] = label })
        }
      }
    }

    function resolveRowLabels() {
      for (const row of rows.value) resolveLabelsForRow(row)
    }

    // --- Load ---
    function endpointFor(parentQid) {
      if (!props.field.statement_endpoint || !parentQid) return null
      return props.field.statement_endpoint.replace(/\{[^}]+\}/, parentQid)
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
    watch(() => props.clearSignal, () => { pendingOps.value = [] })

    // --- Dialog open ---
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
      // If row is a pending add op or pending edit op (has _id)
      // or a saved row that has a pending edit — load the pending edit data
      const src = (row._id !== undefined)
        ? row.data                           // pending op: use its data
        : (pendingEditMap.value[row.statement_id]?.data ?? row)  // saved row: use pending or original
      editingRow.value = (row._id !== undefined)
        ? row
        : (pendingEditMap.value[row.statement_id] ?? row)

      Object.keys(formData).forEach(k => delete formData[k])
      props.field.statement_fields.forEach(f => {
        formData[f.name] = src[f.name] ?? (f.field_type === 'list' ? [] : '')
      })
      dialogError.value = ''
      dialogOpen.value = true
    }

    function closeDialog() {
      dialogOpen.value = false
    }

    // --- Save to pending queue ---
    function saveDialog() {
      const body = { ...formData }
      props.field.statement_fields.forEach(f => {
        if (f.field_type === 'list' && Array.isArray(body[f.name])) {
          body[f.name] = body[f.name].filter(v => v !== '' && v != null)
        }
      })

      if (editingRow.value) {
        if (editingRow.value._id !== undefined) {
          // Updating an existing pending op (add or edit)
          const idx = pendingOps.value.findIndex(op => op._id === editingRow.value._id)
          if (idx >= 0) {
            pendingOps.value.splice(idx, 1, { ...pendingOps.value[idx], data: body, displayRow: body })
          }
        } else {
          // Editing a saved row — add a pending edit op
          const sid = editingRow.value.statement_id
          const existingIdx = pendingOps.value.findIndex(op => op.type === 'edit' && op.statementId === sid)
          if (existingIdx >= 0) {
            pendingOps.value.splice(existingIdx, 1, { ...pendingOps.value[existingIdx], data: body, displayRow: body })
          } else {
            pendingOps.value.push({ _id: ++_nextId, type: 'edit', statementId: sid, data: body, displayRow: body })
          }
        }
      } else {
        pendingOps.value.push({ _id: ++_nextId, type: 'add', data: body, displayRow: body })
      }

      resolveLabelsForRow(body)
      dialogOpen.value = false
      emit('update:pending', props.field.name, pendingOps.value, props.field)
    }

    // --- Delete / undo ---
    function markDelete(row) {
      if (row._id !== undefined) {
        pendingOps.value = pendingOps.value.filter(op => op._id !== row._id)
      } else {
        pendingOps.value.push({ _id: ++_nextId, type: 'delete', statementId: row.statement_id, displayRow: row })
      }
      deleteConfirm.value = null
      emit('update:pending', props.field.name, pendingOps.value, props.field)
    }

    function undoOp(opId) {
      pendingOps.value = pendingOps.value.filter(op => op._id !== opId)
      emit('update:pending', props.field.name, pendingOps.value, props.field)
    }

    // --- Display ---
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

    const isEditingPending = computed(() =>
      editingRow.value && editingRow.value._id !== undefined
    )

    return {
      rows, loading, error, labelMap, pendingOps,
      pendingDeleteIds, pendingEditMap, pendingAdds,
      dialogOpen, editingRow, formData, dialogError, deleteConfirm,
      openNew, openEdit, closeDialog, saveDialog, markDelete, undoOp,
      displayValue, visibleCols, isEditingPending,
    }
  },
  template: `
    <div>
      <div v-if="error" class="error-banner">{{ error }}</div>

      <div v-if="loading">
        <span class="spinner"></span> Loading…
      </div>

      <table v-else-if="rows.length || pendingAdds.length" class="stmt-table">
        <thead>
          <tr>
            <th v-for="f in visibleCols" :key="f.name">{{ f.label }}</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <!-- Saved rows -->
          <tr v-for="row in rows" :key="row.statement_id"
              :style="pendingDeleteIds.has(row.statement_id) ? 'opacity:0.45;text-decoration:line-through' : ''">
            <td v-for="f in visibleCols" :key="f.name">
              {{ displayValue(pendingEditMap[row.statement_id]?.displayRow ?? row, f) }}
            </td>
            <td>
              <template v-if="pendingDeleteIds.has(row.statement_id)">
                <button class="outline" style="padding:0.2rem 0.6rem;margin:0"
                        @click="undoOp(pendingOps.find(op=>op.statementId===row.statement_id)?._id)">Undo</button>
              </template>
              <template v-else>
                <button class="outline" style="padding:0.2rem 0.6rem;margin:0 0.25rem 0 0" @click="openEdit(row)">Edit</button>
                <span v-if="pendingEditMap[row.statement_id]" style="color:orange;font-size:0.8em;margin-right:0.25rem">⚠</span>
                <template v-if="deleteConfirm === row">
                  <small>Sure? </small>
                  <button style="padding:0.2rem 0.5rem;margin:0 0.25rem 0 0" @click="markDelete(row)">Yes</button>
                  <button class="secondary outline" style="padding:0.2rem 0.5rem;margin:0" @click="deleteConfirm=null">No</button>
                </template>
                <button v-else class="secondary outline" style="padding:0.2rem 0.6rem;margin:0" @click="deleteConfirm=row">Remove</button>
              </template>
            </td>
          </tr>

          <!-- Pending add rows -->
          <tr v-for="op in pendingAdds" :key="op._id" style="color:var(--muted-color);font-style:italic">
            <td v-for="f in visibleCols" :key="f.name">{{ displayValue(op.displayRow, f) }}</td>
            <td>
              <button class="outline" style="padding:0.2rem 0.6rem;margin:0 0.25rem 0 0" @click="openEdit(op)">Edit</button>
              <button class="secondary outline" style="padding:0.2rem 0.6rem;margin:0 0.25rem 0 0" @click="undoOp(op._id)">Remove</button>
              <span style="color:orange;font-size:0.8em">⚠ pending</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else><em>No entries yet.</em></p>

      <button class="outline" style="margin-top:0.5rem" @click="openNew">+ Add {{ field.label }}</button>

      <!-- Dialog -->
      <dialog :open="dialogOpen">
        <article style="overflow: visible">
          <header>
            <button rel="prev" @click="closeDialog"></button>
            <strong>{{ isEditingPending || (editingRow && editingRow.statement_id) ? 'Edit' : 'Add' }} {{ field.label }}</strong>
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
              <button type="submit">Save</button>
            </footer>
          </form>
        </article>
      </dialog>
    </div>
  `
}
