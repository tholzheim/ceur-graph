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

    function toComparableString(value) {
      if (value == null) return null;
      return Array.isArray(value) ? value.join(", ") : String(value);
    }

    // Build a map of base-field-name → reference_fields for sources filtering / counting.
    const referenceFieldsByName = computed(() => {
      const m = {};
      for (const f of props.entityConfig?.fields ?? []) {
        if (f.supports_references) m[f.name] = f.reference_fields ?? [];
      }
      return m;
    });

    function sourceBlockHasValue(block, refFields) {
      return (refFields || []).some((rf) => {
        const v = block?.[rf.name];
        if (Array.isArray(v)) return v.some((x) => x !== "" && x != null);
        return v !== "" && v != null;
      });
    }

    function filterSourcesValue(value, refFields) {
      if (!Array.isArray(value)) return value;
      // Multivalued: list[list[block]]; single-valued: list[block]. Detect via the first non-null element.
      const firstNonNull = value.find((v) => v != null);
      if (Array.isArray(firstNonNull)) {
        return value.map((inner) =>
          Array.isArray(inner)
            ? inner.filter((b) => sourceBlockHasValue(b, refFields))
            : [],
        );
      }
      return value.filter((b) => sourceBlockHasValue(b, refFields));
    }

    function countNonEmptySources(value, refFields) {
      if (!Array.isArray(value)) return 0;
      const firstNonNull = value.find((v) => v != null);
      if (Array.isArray(firstNonNull)) {
        return value.reduce(
          (sum, inner) =>
            sum +
            (Array.isArray(inner)
              ? inner.filter((b) => sourceBlockHasValue(b, refFields)).length
              : 0),
          0,
        );
      }
      return value.filter((b) => sourceBlockHasValue(b, refFields)).length;
    }

    const changedFields = computed(() => {
      const fields = [];
      for (const [k, v] of Object.entries(props.pendingData)) {
        // `<X>_sources` is shown in its own section below; skip it from the value diff table.
        if (k.endsWith("_sources")) continue;
        const isEmpty =
          v == null || v === "" || (Array.isArray(v) && !v.length);
        const oldVal = props.loadedData?.[k];
        const wasEmpty =
          oldVal == null ||
          oldVal === "" ||
          (Array.isArray(oldVal) && !oldVal.length);
        if (isEmpty && wasEmpty) continue;
        const newStr = isEmpty ? null : toComparableString(v);
        const oldStr = toComparableString(oldVal);
        if (newStr === oldStr) continue;
        fields.push({
          name: k,
          label: k.replace(/_/g, " "),
          oldVal: oldStr,
          newVal: newStr,
        });
      }
      return fields;
    });

    const sourceChanges = computed(() => {
      const changes = [];
      for (const [baseName, refFields] of Object.entries(
        referenceFieldsByName.value,
      )) {
        const key = `${baseName}_sources`;
        const cur = props.pendingData?.[key];
        const old = props.loadedData?.[key];
        const curStr = JSON.stringify(filterSourcesValue(cur, refFields) ?? []);
        const oldStr = JSON.stringify(old ?? []);
        if (curStr === oldStr) continue;
        changes.push({
          name: key,
          label: baseName.replace(/_/g, " "),
          newCount: countNonEmptySources(cur, refFields),
          oldCount: countNonEmptySources(old, refFields),
        });
      }
      return changes;
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
      () =>
        changedFields.value.length > 0 ||
        statementChanges.value.length > 0 ||
        sourceChanges.value.length > 0,
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

    function opIcon(op) {
      if (op.type === "add") return "plus";
      if (op.type === "edit") return "pencil";
      return "trash";
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
        const refMap = referenceFieldsByName.value;
        for (const [k, v] of Object.entries(props.pendingData)) {
          // `<X>_sources` companions: filter empty source blocks; only include when there's a change.
          if (k.endsWith("_sources")) {
            const baseName = k.slice(0, -"_sources".length);
            const refFields = refMap[baseName];
            if (!refFields) continue;
            const filtered = filterSourcesValue(v, refFields);
            const oldFiltered = filterSourcesValue(
              props.loadedData?.[k],
              refFields,
            );
            if (
              JSON.stringify(filtered ?? []) ===
              JSON.stringify(oldFiltered ?? [])
            )
              continue;
            body[k] = filtered;
            continue;
          }
          const isEmpty =
            v === null ||
            v === undefined ||
            v === "" ||
            (Array.isArray(v) && !v.length);
          if (isEmpty) {
            if (!props.isNew) {
              const oldVal = props.loadedData?.[k];
              const wasEmpty =
                oldVal == null ||
                oldVal === "" ||
                (Array.isArray(oldVal) && !oldVal.length);
              if (!wasEmpty) body[k] = null;
            }
            continue;
          }
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
      sourceChanges,
      hasChanges,
      formatOpDisplay,
      opLabel,
      opIcon,
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

          <!-- Source (reference-block) changes -->
          <template v-if="sourceChanges.length">
            <p style="margin-top:1rem;margin-bottom:0.5rem"><strong>{{ t('commit_sources_heading') }}</strong></p>
            <table class="diff-table">
              <thead><tr><th>{{ t('commit_col_field') }}</th><th v-if="!isNew">{{ t('commit_col_current') }}</th><th>{{ t('commit_col_new') }}</th></tr></thead>
              <tbody>
                <tr v-for="sc in sourceChanges" :key="sc.name">
                  <td>{{ sc.label }}</td>
                  <td v-if="!isNew" style="color:var(--muted-color)">{{ t('commit_source_count', { count: sc.oldCount }) }}</td>
                  <td><strong>{{ t('commit_source_count', { count: sc.newCount }) }}</strong></td>
                </tr>
              </tbody>
            </table>
          </template>

          <!-- Statement changes -->
          <template v-if="statementChanges.length">
            <p style="margin-top:1rem;margin-bottom:0.5rem"><strong>{{ t('commit_stmt_heading') }}</strong></p>
            <table class="diff-table">
              <thead><tr><th>{{ t('commit_col_section') }}</th><th>{{ t('commit_col_action') }}</th><th>{{ t('commit_col_values') }}</th></tr></thead>
              <tbody>
                <tr v-for="(sc, i) in statementChanges" :key="i">
                  <td>{{ sc.fieldLabel }}</td>
                  <td>
                    <span class="diff-op">
                      <icon :name="opIcon(sc.op)" />
                      {{ opLabel(sc.op) }}
                    </span>
                  </td>
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
