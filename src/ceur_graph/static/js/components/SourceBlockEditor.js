import { useI18n } from "../i18n.js";

// `FieldInput` is registered globally in app.js so it can be referenced here as
// `<field-input>` without a static import — that import would create a circular
// dependency with FieldInput.js, which imports this component.
export default {
  name: "SourceBlockEditor",
  props: {
    referenceFields: { type: Array, required: true },
    modelValue: { type: Array, default: () => [] },
    summaryLabel: { type: String, default: "" },
  },
  emits: ["update:modelValue"],
  setup(props, { emit }) {
    const { t } = useI18n();

    function emptyBlock() {
      const block = {};
      (props.referenceFields || []).forEach((rf) => {
        block[rf.name] = rf.field_type === "list" ? [] : "";
      });
      return block;
    }

    function addBlock() {
      emit("update:modelValue", [...(props.modelValue || []), emptyBlock()]);
    }

    function removeBlock(idx) {
      const next = [...(props.modelValue || [])];
      next.splice(idx, 1);
      emit("update:modelValue", next);
    }

    function updateField(idx, name, value) {
      const next = [...(props.modelValue || [])];
      next[idx] = { ...next[idx], [name]: value };
      emit("update:modelValue", next);
    }

    return { t, addBlock, removeBlock, updateField };
  },
  template: `
    <details class="sources-section" style="margin-top:0.5rem">
      <summary style="cursor:pointer">
        {{ summaryLabel || t('stmt_sources_section') }}
        <span v-if="modelValue?.length" style="color:var(--muted-color)">({{ modelValue.length }})</span>
      </summary>
      <div v-for="(src, idx) in (modelValue || [])" :key="idx" class="source-block"
           style="border:1px solid var(--muted-border-color, var(--card-sectionning-background-color));padding:0.5rem 0.75rem;margin:0.5rem 0;border-radius:4px">
        <div v-for="rf in referenceFields" :key="rf.name" class="field-row">
          <label>
            {{ rf.label }}
            <field-input :field="rf" :model-value="src[rf.name]" @update:model-value="updateField(idx, rf.name, $event)" />
          </label>
        </div>
        <button class="secondary outline" type="button" style="padding:0.2rem 0.6rem;margin:0.25rem 0 0" @click="removeBlock(idx)">{{ t('stmt_remove_source') }}</button>
      </div>
      <button class="outline" type="button" style="padding:0.3rem 0.8rem;margin-top:0.5rem" @click="addBlock">{{ t('stmt_add_source') }}</button>
    </details>
  `,
};
