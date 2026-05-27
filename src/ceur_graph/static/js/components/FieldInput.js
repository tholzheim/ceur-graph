import { useI18n } from "../i18n.js";
import ItemSearchInput from "./ItemSearchInput.js";
import SourceBlockEditor from "./SourceBlockEditor.js";

export default {
  name: "FieldInput",
  components: { ItemSearchInput, SourceBlockEditor },
  props: {
    field: { type: Object, required: true },
    modelValue: { default: null },
    // Single-valued field: list[block]. Multivalued field: list[list[block]] (positional with modelValue).
    sources: { default: null },
  },
  emits: ["update:modelValue", "update:sources"],
  setup(props, { emit }) {
    const { computed } = Vue;
    const { t } = useI18n();

    const isItem = computed(
      () => props.field.wikibase_type === "wikibase-item",
    );
    const isNumber = computed(() => props.field.wikibase_type === "quantity");
    const isUrl = computed(() => props.field.wikibase_type === "url");
    const isList = computed(() => props.field.field_type === "list");
    const supportsRefs = computed(() => !!props.field.supports_references);

    const inputType = computed(() => {
      if (isNumber.value) return "number";
      if (isUrl.value) return "url";
      return "text";
    });

    const listVal = computed(() => {
      if (!isList.value) return [];
      return Array.isArray(props.modelValue)
        ? props.modelValue
        : props.modelValue
          ? [props.modelValue]
          : [""];
    });

    const singleSources = computed(() =>
      Array.isArray(props.sources) ? props.sources : [],
    );

    function updateList(idx, newVal) {
      const arr = [...listVal.value];
      arr[idx] = newVal;
      emit("update:modelValue", arr);
    }

    function addListItem() {
      emit("update:modelValue", [...listVal.value, ""]);
      if (supportsRefs.value) {
        const next = Array.isArray(props.sources) ? [...props.sources] : [];
        next.push([]);
        emit("update:sources", next);
      }
    }

    function removeListItem(idx) {
      const arr = listVal.value.filter((_, i) => i !== idx);
      emit("update:modelValue", arr.length ? arr : [""]);
      if (supportsRefs.value) {
        const next = Array.isArray(props.sources) ? [...props.sources] : [];
        next.splice(idx, 1);
        emit("update:sources", next);
      }
    }

    function sourcesForIndex(idx) {
      if (!Array.isArray(props.sources)) return [];
      return Array.isArray(props.sources[idx]) ? props.sources[idx] : [];
    }

    function updateSourcesForIndex(idx, blocks) {
      const next = Array.isArray(props.sources) ? [...props.sources] : [];
      while (next.length <= idx) next.push([]);
      next[idx] = blocks;
      emit("update:sources", next);
    }

    function onSingle(e) {
      const v = e.target ? e.target.value : e;
      emit(
        "update:modelValue",
        isNumber.value ? (v === "" ? null : Number(v)) : v,
      );
    }

    return {
      isItem,
      isNumber,
      isUrl,
      isList,
      inputType,
      listVal,
      supportsRefs,
      singleSources,
      updateList,
      addListItem,
      removeListItem,
      sourcesForIndex,
      updateSourcesForIndex,
      onSingle,
      t,
    };
  },
  template: `
    <div>
      <!-- List field -->
      <template v-if="isList">
        <div v-for="(val, idx) in listVal" :key="idx" class="list-field-item-group" style="margin-bottom:0.5rem">
          <div class="list-field-item">
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
          <source-block-editor v-if="supportsRefs"
                               :reference-fields="field.reference_fields"
                               :model-value="sourcesForIndex(idx)"
                               @update:model-value="updateSourcesForIndex(idx, $event)" />
        </div>
        <button class="secondary outline" style="padding:0.3rem 0.75rem" @click.prevent="addListItem">{{ t('field_add_item') }}</button>
      </template>

      <!-- Single item field -->
      <template v-else>
        <item-search-input
          v-if="isItem"
          :model-value="modelValue || ''"
          @update:model-value="$emit('update:modelValue', $event)"
        />
        <input
          v-else
          :type="inputType"
          :value="modelValue ?? ''"
          @input="onSingle"
          style="margin:0"
        />
        <source-block-editor v-if="supportsRefs"
                             :reference-fields="field.reference_fields"
                             :model-value="singleSources"
                             @update:model-value="$emit('update:sources', $event)" />
      </template>
    </div>
  `,
};
