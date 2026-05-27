import { apiFetch } from "../api.js";
import { useI18n } from "../i18n.js";
import { getLabel } from "../labelCache.js";
import FieldInput from "./FieldInput.js";
import SourceBlockEditor from "./SourceBlockEditor.js";

let _nextId = 0;

export default {
  name: "StatementListEditor",
  components: { FieldInput, SourceBlockEditor },
  emits: ["update:pending"],
  props: {
    field: { type: Object, required: true },
    parentQid: { type: String, default: null },
    clearSignal: { type: Number, default: 0 },
  },
  setup(props, { emit }) {
    const { ref, reactive, watch, computed } = Vue;
    const { t } = useI18n();

    const rows = ref([]);
    const loading = ref(false);
    const error = ref("");
    const labelMap = reactive({});

    const pendingOps = ref([]);

    // Dialog state
    const dialogOpen = ref(false);
    const editingRow = ref(null);
    const formData = reactive({});
    const dialogError = ref("");
    const deleteConfirm = ref(null);

    // Snak-type dropdown state (for enforce_unknown_stmt_name statement types)
    const snakType = ref("unknown_value"); // 'value' | 'unknown_value' | 'no_value'

    // --- Derived pending state ---
    const pendingDeleteIds = computed(
      () =>
        new Set(
          pendingOps.value
            .filter((op) => op.type === "delete")
            .map((op) => op.statementId),
        ),
    );
    const pendingEditMap = computed(() =>
      Object.fromEntries(
        pendingOps.value
          .filter((op) => op.type === "edit")
          .map((op) => [op.statementId, op]),
      ),
    );
    const pendingAdds = computed(() =>
      pendingOps.value.filter((op) => op.type === "add"),
    );

    // --- Snak-type helpers ---
    const subjectField = computed(() =>
      props.field.statement_fields.find((f) => f.is_subject),
    );
    const enforceUnknownStmtName = computed(
      () => !!props.field.enforce_unknown_stmt_name,
    );

    function snakTypeFromValue(v) {
      if (v === "somevalue") return "unknown_value";
      if (v === "novalue") return "no_value";
      return "value";
    }

    watch(snakType, (type) => {
      if (!subjectField.value) return;
      if (type === "unknown_value")
        formData[subjectField.value.name] = "somevalue";
      else if (type === "no_value")
        formData[subjectField.value.name] = "novalue";
      else formData[subjectField.value.name] = "";
    });

    // --- Label resolution ---
    function resolveLabelsForRow(row) {
      const itemFields = props.field.statement_fields.filter(
        (f) => f.wikibase_type === "wikibase-item",
      );
      for (const f of itemFields) {
        const qid = row[f.name];
        if (qid && !(qid in labelMap)) {
          getLabel(qid).then((label) => {
            if (label) labelMap[qid] = label;
          });
        }
      }
    }

    function resolveRowLabels() {
      for (const row of rows.value) resolveLabelsForRow(row);
    }

    // --- Load ---
    function endpointFor(parentQid) {
      if (!props.field.statement_endpoint || !parentQid) return null;
      return props.field.statement_endpoint.replace(/\{[^}]+\}/, parentQid);
    }

    async function load() {
      const url = endpointFor(props.parentQid);
      if (!url) return;
      loading.value = true;
      error.value = "";
      try {
        rows.value = (await apiFetch(url)) || [];
        resolveRowLabels();
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    }

    watch(() => props.parentQid, load, { immediate: true });
    watch(
      () => props.clearSignal,
      () => {
        pendingOps.value = [];
      },
    );

    // --- Sources (Wikibase reference blocks) helpers ---
    function emptySource() {
      const block = {};
      (props.field.reference_fields || []).forEach((rf) => {
        block[rf.name] = rf.field_type === "list" ? [] : "";
      });
      return block;
    }

    function cloneSources(srcArr) {
      if (!Array.isArray(srcArr)) return [];
      return srcArr.map((s) => ({ ...emptySource(), ...s }));
    }

    function sourceBlockHasValue(block) {
      return (props.field.reference_fields || []).some((rf) => {
        const v = block?.[rf.name];
        if (Array.isArray(v)) return v.some((x) => x !== "" && x != null);
        return v !== "" && v != null;
      });
    }

    function effectiveSources(row) {
      if (!row) return [];
      const sid = row.statement_id;
      const edit = sid ? pendingEditMap.value[sid] : null;
      const eff = edit?.displayRow ?? row.displayRow ?? row;
      return Array.isArray(eff?.sources) ? eff.sources : [];
    }

    // --- Dialog open ---
    function openNew() {
      editingRow.value = null;
      Object.keys(formData).forEach((k) => delete formData[k]);
      props.field.statement_fields.forEach((f) => {
        formData[f.name] = f.field_type === "list" ? [] : "";
      });
      formData.sources = [];
      // Default snak type to unknown_value (matches model default of "somevalue")
      snakType.value = "unknown_value";
      if (subjectField.value) formData[subjectField.value.name] = "somevalue";
      dialogError.value = "";
      dialogOpen.value = true;
    }

    function openEdit(row) {
      const src =
        row._id !== undefined
          ? row.data
          : (pendingEditMap.value[row.statement_id]?.data ?? row);
      editingRow.value =
        row._id !== undefined
          ? row
          : (pendingEditMap.value[row.statement_id] ?? row);

      Object.keys(formData).forEach((k) => delete formData[k]);
      props.field.statement_fields.forEach((f) => {
        formData[f.name] = src[f.name] ?? (f.field_type === "list" ? [] : "");
      });
      formData.sources = cloneSources(src.sources);
      if (subjectField.value && enforceUnknownStmtName.value) {
        snakType.value = snakTypeFromValue(src[subjectField.value.name] ?? "");
      }
      dialogError.value = "";
      dialogOpen.value = true;
    }

    function closeDialog() {
      dialogOpen.value = false;
    }

    // --- Save to pending queue ---
    function saveDialog() {
      const body = { ...formData };
      props.field.statement_fields.forEach((f) => {
        if (f.field_type === "list" && Array.isArray(body[f.name])) {
          body[f.name] = body[f.name].filter((v) => v !== "" && v != null);
        }
      });
      if (props.field.supports_references) {
        body.sources = (formData.sources || []).filter(sourceBlockHasValue);
      } else {
        delete body.sources;
      }

      if (editingRow.value) {
        if (editingRow.value._id !== undefined) {
          const idx = pendingOps.value.findIndex(
            (op) => op._id === editingRow.value._id,
          );
          if (idx >= 0) {
            pendingOps.value.splice(idx, 1, {
              ...pendingOps.value[idx],
              data: body,
              displayRow: body,
            });
          }
        } else {
          const sid = editingRow.value.statement_id;
          const existingIdx = pendingOps.value.findIndex(
            (op) => op.type === "edit" && op.statementId === sid,
          );
          if (existingIdx >= 0) {
            pendingOps.value.splice(existingIdx, 1, {
              ...pendingOps.value[existingIdx],
              data: body,
              displayRow: body,
            });
          } else {
            pendingOps.value.push({
              _id: ++_nextId,
              type: "edit",
              statementId: sid,
              data: body,
              displayRow: body,
            });
          }
        }
      } else {
        pendingOps.value.push({
          _id: ++_nextId,
          type: "add",
          data: body,
          displayRow: body,
        });
      }

      resolveLabelsForRow(body);
      dialogOpen.value = false;
      emit("update:pending", props.field.name, pendingOps.value, props.field);
    }

    // --- Delete / undo ---
    function markDelete(row) {
      if (row._id !== undefined) {
        pendingOps.value = pendingOps.value.filter((op) => op._id !== row._id);
      } else {
        pendingOps.value.push({
          _id: ++_nextId,
          type: "delete",
          statementId: row.statement_id,
          displayRow: row,
        });
      }
      deleteConfirm.value = null;
      emit("update:pending", props.field.name, pendingOps.value, props.field);
    }

    function undoOp(opId) {
      pendingOps.value = pendingOps.value.filter((op) => op._id !== opId);
      emit("update:pending", props.field.name, pendingOps.value, props.field);
    }

    // --- Display ---
    function displayValue(row, f) {
      const v = row[f.name];
      if (v == null || v === "") return "—";
      if (Array.isArray(v)) return v.join(", ") || "—";
      if (f.is_subject) {
        if (v === "somevalue") return t("stmt_display_unknown");
        if (v === "novalue") return t("stmt_display_no_value");
      }
      if (f.wikibase_type === "wikibase-item")
        return labelMap[v] ? `${labelMap[v]} (${v})` : v;
      return String(v);
    }

    const visibleCols = computed(() => props.field.statement_fields);

    const isEditingPending = computed(
      () => editingRow.value && editingRow.value._id !== undefined,
    );

    return {
      rows,
      loading,
      error,
      labelMap,
      pendingOps,
      pendingDeleteIds,
      pendingEditMap,
      pendingAdds,
      dialogOpen,
      editingRow,
      formData,
      dialogError,
      deleteConfirm,
      openNew,
      openEdit,
      closeDialog,
      saveDialog,
      markDelete,
      undoOp,
      displayValue,
      visibleCols,
      isEditingPending,
      snakType,
      subjectField,
      enforceUnknownStmtName,
      effectiveSources,
      t,
    };
  },
  template: `
    <div>
      <div v-if="error" class="error-banner">{{ error }}</div>

      <div v-if="loading">
        <span class="spinner"></span> {{ t('stmt_loading') }}
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
                        @click="undoOp(pendingOps.find(op=>op.statementId===row.statement_id)?._id)">{{ t('stmt_undo_button') }}</button>
              </template>
              <template v-else>
                <button class="outline" style="padding:0.2rem 0.6rem;margin:0 0.25rem 0 0" @click="openEdit(row)">{{ t('stmt_edit_button') }}</button>
                <span v-if="effectiveSources(row).length" :title="t('stmt_source_count', { count: effectiveSources(row).length })" style="font-size:0.85em;margin-right:0.25rem">📚 {{ effectiveSources(row).length }}</span>
                <span v-if="pendingEditMap[row.statement_id]" style="color:orange;font-size:0.8em;margin-right:0.25rem">⚠</span>
                <template v-if="deleteConfirm === row">
                  <small>{{ t('stmt_delete_confirm') }} </small>
                  <button style="padding:0.2rem 0.5rem;margin:0 0.25rem 0 0" @click="markDelete(row)">{{ t('stmt_delete_yes') }}</button>
                  <button class="secondary outline" style="padding:0.2rem 0.5rem;margin:0" @click="deleteConfirm=null">{{ t('stmt_delete_no') }}</button>
                </template>
                <button v-else class="secondary outline" style="padding:0.2rem 0.6rem;margin:0" @click="deleteConfirm=row">{{ t('stmt_remove_button') }}</button>
              </template>
            </td>
          </tr>

          <!-- Pending add rows -->
          <tr v-for="op in pendingAdds" :key="op._id" style="color:var(--muted-color);font-style:italic">
            <td v-for="f in visibleCols" :key="f.name">{{ displayValue(op.displayRow, f) }}</td>
            <td>
              <button class="outline" style="padding:0.2rem 0.6rem;margin:0 0.25rem 0 0" @click="openEdit(op)">{{ t('stmt_edit_button') }}</button>
              <button class="secondary outline" style="padding:0.2rem 0.6rem;margin:0 0.25rem 0 0" @click="undoOp(op._id)">{{ t('stmt_remove_button') }}</button>
              <span v-if="op.displayRow?.sources?.length" :title="t('stmt_source_count', { count: op.displayRow.sources.length })" style="font-size:0.85em;margin-right:0.25rem">📚 {{ op.displayRow.sources.length }}</span>
              <span style="color:orange;font-size:0.8em">{{ t('stmt_pending') }}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else><em>{{ t('stmt_empty') }}</em></p>

      <button class="outline" style="margin-top:0.5rem" @click="openNew">{{ t('stmt_add_button', { label: field.label }) }}</button>

      <!-- Dialog -->
      <dialog :open="dialogOpen">
        <article style="overflow: visible">
          <header>
            <button rel="prev" @click="closeDialog"></button>
            <strong>{{ isEditingPending || (editingRow && editingRow.statement_id) ? t('stmt_dialog_edit', { label: field.label }) : t('stmt_dialog_add', { label: field.label }) }}</strong>
          </header>
          <div v-if="dialogError" class="error-banner">{{ dialogError }}</div>
          <form @submit.prevent="saveDialog">
            <template v-for="f in field.statement_fields" :key="f.name">

              <!-- Subject field: snak-type dropdown + conditional QID input -->
              <template v-if="f.is_subject && enforceUnknownStmtName">
                <div class="field-row">
                  <label>
                    {{ t('stmt_snak_type') }}
                    <select v-model="snakType" style="margin:0">
                      <option value="value">{{ t('stmt_snak_value') }}</option>
                      <option value="unknown_value">{{ t('stmt_snak_unknown') }}</option>
                      <option value="no_value">{{ t('stmt_snak_no_value') }}</option>
                    </select>
                  </label>
                </div>
                <div v-if="snakType === 'value'" class="field-row">
                  <label>
                    {{ f.label }}<span style="color:red">*</span>
                    <field-input :field="f" v-model="formData[f.name]" />
                  </label>
                </div>
              </template>

              <!-- object_named_as: only visible when snak type is unknown_value (if enforce) -->
              <template v-else-if="f.is_object_named_as && enforceUnknownStmtName">
                <div v-if="snakType === 'unknown_value'" class="field-row">
                  <label>
                    {{ f.label }}<span style="color:red">*</span>
                    <field-input :field="f" v-model="formData[f.name]" />
                  </label>
                </div>
              </template>

              <!-- All other fields shown normally; also all fields when !enforceUnknownStmtName -->
              <div v-else class="field-row">
                <label>
                  {{ f.label }}<span v-if="f.required" style="color:red">*</span>
                  <field-input :field="f" v-model="formData[f.name]" />
                </label>
              </div>

            </template>

            <!-- Wikibase reference blocks (provenance) — collapsed by default -->
            <source-block-editor v-if="field.supports_references"
                                 :reference-fields="field.reference_fields"
                                 v-model="formData.sources" />


            <footer>
              <button class="secondary outline" type="button" @click="closeDialog">{{ t('stmt_cancel_button') }}</button>
              <button type="submit">{{ t('stmt_save_button') }}</button>
            </footer>
          </form>
        </article>
      </dialog>
    </div>
  `,
};
