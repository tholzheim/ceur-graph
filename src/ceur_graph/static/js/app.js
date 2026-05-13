import { computed, createApp, nextTick, onMounted, reactive, ref, watch } from "vue";
import { apiFetch } from "./api.js";
import EntityEditor from "./components/EntityEditor.js";
import LoginForm from "./components/LoginForm.js";
import { useI18n } from "./i18n.js";

// Expose Vue composition API globally so component files can do `const { ref } = Vue`
window.Vue = { ref, reactive, computed, watch, nextTick, onMounted };

const App = {
  components: { LoginForm, EntityEditor },
  setup() {
    const { t } = useI18n();

    const state = reactive({
      token: localStorage.getItem("token"),
      schema: null,
      schemaError: null,
    });

    const isLoggedIn = computed(() => !!state.token);

    async function loadSchema() {
      if (!isLoggedIn.value) return;
      try {
        state.schema = await apiFetch("/api/schema/entities");
      } catch (e) {
        state.schemaError = e.message;
      }
    }

    function onLogin(token) {
      state.token = token;
      state.schemaError = null;
      loadSchema();
    }

    function onLogout() {
      state.token = null;
      state.schema = null;
      state.schemaError = null;
    }

    loadSchema();

    return { state, isLoggedIn, onLogin, onLogout, t };
  },
  template: `
    <login-form v-if="!isLoggedIn" @login="onLogin" />
    <div v-else-if="!state.schema && !state.schemaError" style="padding:2rem;text-align:center">
      <span class="spinner"></span> {{ t('app_loading_schema') }}
    </div>
    <div v-else-if="state.schemaError" class="error-banner" style="margin:2rem">
      {{ t('app_schema_error', { error: state.schemaError }) }}
    </div>
    <entity-editor v-else :schema="state.schema" @logout="onLogout" />
  `,
};

createApp(App).mount("#app");
