import { apiFetch } from '../api.js'
import FieldInput from './FieldInput.js'
import StatementListEditor from './StatementListEditor.js'
import CommitDialog from './CommitDialog.js'

export default {
  name: 'EntityEditor',
  components: { FieldInput, StatementListEditor, CommitDialog },
  props: {
    schema: { default: null },
  },
  emits: ['logout'],
  setup(props, { emit }) {
    const { ref, reactive, computed, watch } = Vue

    const selectedEntityName = ref('')
    const qidInput = ref('')
    const loadedData = ref(null)
    const pendingData = reactive({})
    const isNew = ref(false)
    const loadError = ref('')
    const loadLoading = ref(false)
    const success = ref('')
    const commitOpen = ref(false)

    // Pending statement changes collected from child StatementListEditors
    const pendingStatements = reactive({})
    const clearSignal = ref(0)

    // schema is the flat list returned by /api/schema/entities
    const entities = computed(() => Array.isArray(props.schema) ? props.schema : (props.schema?.entities ?? []))
    const selectedEntity = computed(() =>
      entities.value.find(e => e.name === selectedEntityName.value) ?? null
    )
    const simpleFields = computed(() =>
      (selectedEntity.value?.fields ?? []).filter(f => f.field_type !== 'statement_list')
    )
    const statementFields = computed(() =>
      (selectedEntity.value?.fields ?? []).filter(f => f.field_type === 'statement_list')
    )
    const loadedQid = computed(() => loadedData.value?.qid ?? null)

    function resetForm() {
      loadedData.value = null
      Object.keys(pendingData).forEach(k => delete pendingData[k])
      Object.keys(pendingStatements).forEach(k => delete pendingStatements[k])
      clearSignal.value++
      if (selectedEntity.value) {
        selectedEntity.value.fields.forEach(f => {
          if (f.field_type === 'statement_list') return
          pendingData[f.name] = f.field_type === 'list' ? [] : ''
        })
      }
      loadError.value = ''
      success.value = ''
    }

    watch(selectedEntityName, () => {
      qidInput.value = ''
      isNew.value = false
      resetForm()
    })

    async function load() {
      if (!selectedEntity.value || !qidInput.value.trim()) return
      loadLoading.value = true
      loadError.value = ''
      try {
        const prefix = selectedEntity.value.endpoint_prefix
        const data = await apiFetch(`${prefix}/${qidInput.value.trim()}`)
        if (!data) return
        loadedData.value = data
        isNew.value = false
        Object.keys(pendingStatements).forEach(k => delete pendingStatements[k])
        clearSignal.value++
        Object.keys(pendingData).forEach(k => delete pendingData[k])
        selectedEntity.value.fields.forEach(f => {
          if (f.field_type === 'statement_list') return
          pendingData[f.name] = data[f.name] ?? (f.field_type === 'list' ? [] : '')
        })
      } catch (e) {
        loadError.value = e.message
      } finally {
        loadLoading.value = false
      }
    }

    function startNew() {
      qidInput.value = ''
      isNew.value = true
      resetForm()
    }

    function onPendingChange(fieldName, ops, fieldConfig) {
      if (ops.length === 0) {
        delete pendingStatements[fieldName]
      } else {
        pendingStatements[fieldName] = { ops, field: fieldConfig }
      }
    }

    function onSaved(entity) {
      loadedData.value = entity
      if (entity?.qid) qidInput.value = entity.qid
      isNew.value = false
      // Clear pending statements after successful commit
      Object.keys(pendingStatements).forEach(k => delete pendingStatements[k])
      clearSignal.value++
      success.value = `Saved! QID: ${entity?.qid ?? '(unknown)'}`
      setTimeout(() => { success.value = '' }, 5000)
    }

    function logout() {
      localStorage.removeItem('token')
      emit('logout')
    }

    return {
      entities, selectedEntityName, selectedEntity, simpleFields, statementFields,
      qidInput, loadedData, pendingData, isNew, loadError, loadLoading, success, commitOpen,
      loadedQid, load, startNew, onSaved, logout,
      pendingStatements, clearSignal, onPendingChange,
    }
  },
  template: `
    <div>
      <nav>
        <ul><li><strong>CEUR-WS Entity Editor</strong></li></ul>
        <ul><li><button class="secondary outline" @click="logout" style="padding:0.3rem 0.75rem">Logout</button></li></ul>
      </nav>

      <div class="entity-editor">
        <!-- Entity selector -->
        <div style="display:flex;gap:1rem;align-items:flex-end;margin-bottom:1.5rem;flex-wrap:wrap">
          <label style="flex:1;min-width:180px;margin:0">
            Entity type
            <select v-model="selectedEntityName" style="margin:0">
              <option value="">— Select —</option>
              <option v-for="e in entities" :key="e.name" :value="e.name">{{ e.name }}</option>
            </select>
          </label>

          <label style="flex:1;min-width:200px;margin:0">
            Load existing QID
            <div style="display:flex;gap:0.5rem">
              <input v-model="qidInput" placeholder="Q…" style="margin:0;flex:1" @keyup.enter="load" :disabled="!selectedEntity" />
              <button @click="load" :aria-busy="loadLoading" :disabled="!selectedEntity" style="margin:0;white-space:nowrap">Load</button>
            </div>
          </label>

          <button class="secondary outline" @click="startNew" :disabled="!selectedEntity" style="margin:0;align-self:flex-end">New</button>
        </div>

        <div v-if="loadError" class="error-banner">{{ loadError }}</div>
        <div v-if="success" class="success-banner">{{ success }}</div>

        <!-- Form -->
        <template v-if="selectedEntity && (isNew || loadedData)">
          <hgroup>
            <h3>{{ isNew ? 'New ' + selectedEntity.name : selectedEntity.name + ' — ' + loadedQid }}</h3>
          </hgroup>

          <!-- Simple fields -->
          <div v-for="f in simpleFields" :key="f.name" class="field-row">
            <label>
              {{ f.label }}<span v-if="f.required" style="color:red">*</span>
              <field-input :field="f" v-model="pendingData[f.name]" />
            </label>
          </div>

          <div style="margin:1.5rem 0">
            <button @click="commitOpen = true">Commit changes…</button>
          </div>

          <!-- Statement list editors -->
          <template v-for="f in statementFields" :key="f.name">
            <hr>
            <h4>{{ f.label }}</h4>
            <statement-list-editor
              :field="f"
              :parent-qid="loadedQid"
              :clear-signal="clearSignal"
              @update:pending="(name, ops, fc) => onPendingChange(name, ops, fc)"
            />
          </template>
        </template>

        <p v-else-if="selectedEntity && !isNew && !loadedData" style="color:var(--muted-color)">
          Enter a QID and click Load, or click New to create a new entity.
        </p>
      </div>

      <!-- Commit dialog -->
      <commit-dialog
        :open="commitOpen"
        :pending-data="pendingData"
        :loaded-data="loadedData"
        :is-new="isNew"
        :entity-config="selectedEntity ?? {}"
        :pending-statements="pendingStatements"
        @close="commitOpen = false"
        @saved="onSaved"
      />
    </div>
  `
}
