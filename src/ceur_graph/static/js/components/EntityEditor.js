import { apiFetch } from "../api.js";
import { LANGUAGES, useI18n } from "../i18n.js";
import CommitDialog from "./CommitDialog.js";
import FieldInput from "./FieldInput.js";
import StatementListEditor from "./StatementListEditor.js";

export default {
  name: "EntityEditor",
  components: { FieldInput, StatementListEditor, CommitDialog },
  props: {
    schema: { default: null },
  },
  emits: ["logout"],
  setup(props, { emit }) {
    const { ref, reactive, computed, watch, onMounted, nextTick } = Vue;
    const { t, locale, setLocale } = useI18n();

    const selectedEntityName = ref("");
    const qidInput = ref("");
    const loadedData = ref(null);
    const pendingData = reactive({});
    const isNew = ref(false);
    const loadError = ref("");
    const loadLoading = ref(false);
    const success = ref("");
    const commitOpen = ref(false);

    // Pending statement changes collected from child StatementListEditors
    const pendingStatements = reactive({});
    const clearSignal = ref(0);

    function parseFormUrl() {
      const parts = window.location.pathname.split('/').filter(Boolean);
      if (parts[0] !== 'form') return null;
      return { entitySlug: parts[1] ?? null, action: parts[2] ?? null };
    }

    function pushFormUrl(entitySlug, action = null) {
      const path = action ? `/form/${entitySlug}/${action}` : `/form/${entitySlug}`;
      history.pushState(null, '', path);
    }

    // schema is the flat list returned by /api/schema/entities
    const entities = computed(() =>
      Array.isArray(props.schema)
        ? props.schema
        : (props.schema?.entities ?? []),
    );
    const selectedEntity = computed(
      () =>
        entities.value.find((e) => e.name === selectedEntityName.value) ?? null,
    );
    const simpleFields = computed(() =>
      (selectedEntity.value?.fields ?? []).filter(
        (f) => f.field_type !== "statement_list",
      ),
    );
    const statementFields = computed(() =>
      (selectedEntity.value?.fields ?? []).filter(
        (f) => f.field_type === "statement_list",
      ),
    );
    const loadedQid = computed(() => loadedData.value?.qid ?? null);

    function resetForm() {
      loadedData.value = null;
      Object.keys(pendingData).forEach((k) => delete pendingData[k]);
      Object.keys(pendingStatements).forEach(
        (k) => delete pendingStatements[k],
      );
      clearSignal.value++;
      if (selectedEntity.value) {
        selectedEntity.value.fields.forEach((f) => {
          if (f.field_type === "statement_list") return;
          pendingData[f.name] = f.field_type === "list" ? [] : "";
        });
      }
      loadError.value = "";
      success.value = "";
    }

    let initializing = false;

    watch(selectedEntityName, () => {
      qidInput.value = "";
      isNew.value = false;
      resetForm();
      if (!initializing && selectedEntityName.value) {
        pushFormUrl(selectedEntityName.value.toLowerCase());
      }
    });

    async function load() {
      if (!selectedEntity.value || !qidInput.value.trim()) return;
      loadLoading.value = true;
      loadError.value = "";
      try {
        const prefix = selectedEntity.value.endpoint_prefix;
        const data = await apiFetch(`${prefix}/${qidInput.value.trim()}`);
        if (!data) return;
        loadedData.value = data;
        isNew.value = false;
        pushFormUrl(selectedEntityName.value.toLowerCase(), qidInput.value.trim());
        Object.keys(pendingStatements).forEach(
          (k) => delete pendingStatements[k],
        );
        clearSignal.value++;
        Object.keys(pendingData).forEach((k) => delete pendingData[k]);
        selectedEntity.value.fields.forEach((f) => {
          if (f.field_type === "statement_list") return;
          pendingData[f.name] =
            data[f.name] ?? (f.field_type === "list" ? [] : "");
        });
      } catch (e) {
        loadError.value = e.message;
      } finally {
        loadLoading.value = false;
      }
    }

    function startNew() {
      qidInput.value = "";
      isNew.value = true;
      resetForm();
      if (selectedEntityName.value) {
        pushFormUrl(selectedEntityName.value.toLowerCase(), 'new');
      }
    }

    function onPendingChange(fieldName, ops, fieldConfig) {
      if (ops.length === 0) {
        delete pendingStatements[fieldName];
      } else {
        pendingStatements[fieldName] = { ops, field: fieldConfig };
      }
    }

    function onSaved(entity) {
      loadedData.value = entity;
      if (entity?.qid) {
        qidInput.value = entity.qid;
        history.replaceState(null, '', `/form/${selectedEntityName.value.toLowerCase()}/${entity.qid}`);
      }
      isNew.value = false;
      // Clear pending statements after successful commit
      Object.keys(pendingStatements).forEach(
        (k) => delete pendingStatements[k],
      );
      clearSignal.value++;
      success.value = t("entity_saved", { qid: entity?.qid ?? "(unknown)" });
      setTimeout(() => {
        success.value = "";
      }, 5000);
    }

    function logout() {
      localStorage.removeItem("token");
      emit("logout");
    }

    onMounted(async () => {
      const parsed = parseFormUrl();
      if (!parsed?.entitySlug) return;
      const match = entities.value.find(
        (e) => e.name.toLowerCase() === parsed.entitySlug.toLowerCase(),
      );
      if (!match) return;
      initializing = true;
      selectedEntityName.value = match.name;
      await nextTick();
      initializing = false;
      if (parsed.action === 'new') {
        startNew();
      } else if (parsed.action) {
        qidInput.value = parsed.action;
        await load();
      }
    });

    return {
      entities,
      selectedEntityName,
      selectedEntity,
      simpleFields,
      statementFields,
      qidInput,
      loadedData,
      pendingData,
      isNew,
      loadError,
      loadLoading,
      success,
      commitOpen,
      loadedQid,
      load,
      startNew,
      onSaved,
      logout,
      pendingStatements,
      clearSignal,
      onPendingChange,
      t,
      locale,
      setLocale,
      LANGUAGES,
    };
  },
  template: `
    <div>
      <nav>
        <ul><li><strong>{{ t('nav_title') }}</strong></li></ul>
        <ul>
          <li>
            <select :value="locale" @change="setLocale($event.target.value)" style="width:auto;margin:0 0.5rem 0 0">
              <option v-for="(label, code) in LANGUAGES" :key="code" :value="code">{{ label }}</option>
            </select>
          </li>
          <li><button class="secondary outline" @click="logout" style="padding:0.3rem 0.75rem">{{ t('nav_logout') }}</button></li>
        </ul>
      </nav>

      <div class="entity-editor">
        <!-- Entity selector -->
        <div style="display:flex;gap:1rem;align-items:flex-end;margin-bottom:1.5rem;flex-wrap:wrap">
          <label style="flex:1;min-width:180px;margin:0">
            {{ t('entity_type_label') }}
            <select v-model="selectedEntityName" style="margin:0">
              <option value="">{{ t('entity_type_placeholder') }}</option>
              <option v-for="e in entities" :key="e.name" :value="e.name">{{ e.name }}</option>
            </select>
          </label>

          <label style="flex:1;min-width:200px;margin:0">
            {{ t('entity_load_label') }}
            <div style="display:flex;gap:0.5rem">
              <input v-model="qidInput" :placeholder="t('entity_load_placeholder')" style="margin:0;flex:1" @keyup.enter="load" :disabled="!selectedEntity" />
              <button @click="load" :aria-busy="loadLoading" :disabled="!selectedEntity" style="margin:0;white-space:nowrap">{{ t('entity_load_button') }}</button>
            </div>
          </label>

          <button class="secondary outline" @click="startNew" :disabled="!selectedEntity" style="margin:0;align-self:flex-end">{{ t('entity_new_button') }}</button>
        </div>

        <div v-if="loadError" class="error-banner">{{ loadError }}</div>
        <div v-if="success" class="success-banner">{{ success }}</div>

        <!-- Form -->
        <template v-if="selectedEntity && (isNew || loadedData)">
          <hgroup>
            <h3>{{ isNew ? t('entity_new_heading', { name: selectedEntity.name }) : t('entity_loaded_heading', { name: selectedEntity.name, qid: loadedQid }) }}</h3>
          </hgroup>

          <!-- Simple fields -->
          <div v-for="f in simpleFields" :key="f.name" class="field-row">
            <label>
              {{ f.label }}<span v-if="f.required" style="color:red">*</span>
              <field-input :field="f" v-model="pendingData[f.name]" />
            </label>
          </div>

          <div style="margin:1.5rem 0">
            <button @click="commitOpen = true">{{ t('entity_commit_button') }}</button>
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
          {{ t('entity_empty_hint') }}
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
  `,
};
