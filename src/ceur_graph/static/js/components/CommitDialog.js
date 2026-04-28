import { apiDelete, apiPost, apiPut } from "../api.js";
import { useI18n } from "../i18n.js";

export default {
  name: "CommitDialog",
  props: {
    open: { type: Boolean, default: false },
    pendingData: { type: Object, required: true },
    loadedData: { type: Object, default: null },
    isNew: { type: Boolean, default: false },
    entityConfig: { type: Object, required: true },
    pendingStatements: { type: Object, default: () => ({}) },
  },
  emits: ["close", "saved"],
  setup(props, { emit }) {
    const { computed, ref } = Vue;
    const { t } = useI18n();

    const loading = ref(false);
    const error = ref("");

    const changedFields = computed(() => {
      const fields = [];
      for (const [k, v] of Object.entries(props.pendingData)) {
        if (v == null || v === "" || (Array.isArray(v) && !v.length)) continue;
        const oldVal = props.loadedData?.[k];
        const newStr = Array.isArray(v) ? v.join(", ") : String(v);
        const oldStr =
          oldVal != null
            ? Array.isArray(oldVal)
              ? oldVal.join(", ")
              : String(oldVal)
            : null;
        if (newStr !== oldStr) {
          fields.push({
            name: k,
            label: k.replace(/_/g, " "),
            oldVal: oldStr,
            newVal: newStr,
          });
        }
      }
      return fields;
    });

    const statementChanges = computed(() => {
      const changes = [];
      for (const [, { ops, field }] of Object.entries(
        props.pendingStatements,
      )) {
        for (const op of ops) {
          changes.push({ fieldLabel: field.label, op });
        }
      }
      return changes;
    });

    const hasChanges = computed(
      () => changedFields.value.length > 0 || statementChanges.value.length > 0,
    );

    function formatOpDisplay(op) {
      if (op.type === "delete") return "—";
      return Object.entries(op.data || {})
        .filter(
          ([, v]) => v !== "" && v != null && !(Array.isArray(v) && !v.length),
        )
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
        .join(" · ");
    }

    function opLabel(op) {
      if (op.type === "add") return t("commit_op_add");
      if (op.type === "edit") return t("commit_op_edit");
      return t("commit_op_remove");
    }

    function close() {
      error.value = "";
      emit("close");
    }

    async function confirm() {
      loading.value = true;
      error.value = "";
      try {
        const prefix = props.entityConfig.endpoint_prefix;
        const body = {};
        for (const [k, v] of Object.entries(props.pendingData)) {
          if (
            v === null ||
            v === undefined ||
            v === "" ||
            (Array.isArray(v) && !v.length)
          )
            continue;
          body[k] = v;
        }
        let result;
        if (props.isNew) {
          result = await apiPost(`${prefix}/`, body);
        } else {
          const qid = props.loadedData?.qid;
          result = await apiPut(`${prefix}/${qid}`, body);
        }

        // Execute pending statement operations using the (possibly new) entity QID
        const entityQid = result?.qid ?? props.loadedData?.qid;
        if (entityQid) {
          for (const [, { ops, field }] of Object.entries(
            props.pendingStatements,
          )) {
            const url = field.statement_endpoint?.replace(
              /\{[^}]+\}/,
              entityQid,
            );
            if (!url) continue;
            for (const op of ops) {
              if (op.type === "add") await apiPost(`${url}/`, op.data);
              else if (op.type === "edit")
                await apiPut(`${url}/${op.statementId}`, op.data);
              else if (op.type === "delete")
                await apiDelete(`${url}/${op.statementId}`);
            }
          }
        }

        emit("saved", result);
        close();
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    }

    return {
      changedFields,
      statementChanges,
      hasChanges,
      formatOpDisplay,
      opLabel,
      loading,
      error,
      close,
      confirm,
      t,
    };
  },
  template: `
    <dialog :open="open">
      <article>
        <header>
          <button rel="prev" @click="close"></button>
          <strong>{{ isNew ? t('commit_title_create', { name: entityConfig.name }) : t('commit_title_update', { name: entityConfig.name }) }}</strong>
        </header>

        <div v-if="error" class="error-banner">{{ error }}</div>

        <p v-if="!hasChanges"><em>{{ t('commit_no_changes') }}</em></p>
        <template v-else>
          <p>{{ t('commit_review') }}</p>

          <!-- Field changes -->
          <table v-if="changedFields.length" class="diff-table">
            <thead><tr><th>{{ t('commit_col_field') }}</th><th v-if="!isNew">{{ t('commit_col_current') }}</th><th>{{ t('commit_col_new') }}</th></tr></thead>
            <tbody>
              <tr v-for="f in changedFields" :key="f.name">
                <td>{{ f.label }}</td>
                <td v-if="!isNew" style="color:var(--muted-color)">{{ f.oldVal ?? '—' }}</td>
                <td><strong>{{ f.newVal }}</strong></td>
              </tr>
            </tbody>
          </table>

          <!-- Statement changes -->
          <template v-if="statementChanges.length">
            <p style="margin-top:1rem;margin-bottom:0.5rem"><strong>{{ t('commit_stmt_heading') }}</strong></p>
            <table class="diff-table">
              <thead><tr><th>{{ t('commit_col_section') }}</th><th>{{ t('commit_col_action') }}</th><th>{{ t('commit_col_values') }}</th></tr></thead>
              <tbody>
                <tr v-for="(sc, i) in statementChanges" :key="i">
                  <td>{{ sc.fieldLabel }}</td>
                  <td>{{ opLabel(sc.op) }}</td>
                  <td>{{ formatOpDisplay(sc.op) }}</td>
                </tr>
              </tbody>
            </table>
          </template>
        </template>

        <footer>
          <button class="secondary outline" @click="close">{{ t('commit_cancel') }}</button>
          <button @click="confirm" :aria-busy="loading" :disabled="!hasChanges">
            {{ t('commit_confirm') }}
          </button>
        </footer>
      </article>
    </dialog>
  `,
};
