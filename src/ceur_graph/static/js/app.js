import { createApp, ref, reactive, computed, watch, nextTick } from 'vue'
import { apiFetch } from './api.js'
import LoginForm from './components/LoginForm.js'
import EntityEditor from './components/EntityEditor.js'

// Expose Vue composition API globally so component files can do `const { ref } = Vue`
window.Vue = { ref, reactive, computed, watch, nextTick }

const App = {
  components: { LoginForm, EntityEditor },
  setup() {
    const state = reactive({
      token: localStorage.getItem('token'),
      schema: null,
      schemaError: null,
    })

    const isLoggedIn = computed(() => !!state.token)

    async function loadSchema() {
      if (!isLoggedIn.value) return
      try {
        state.schema = await apiFetch('/api/schema/entities')
      } catch (e) {
        state.schemaError = e.message
      }
    }

    function onLogin(token) {
      state.token = token
      state.schemaError = null
      loadSchema()
    }

    function onLogout() {
      state.token = null
      state.schema = null
      state.schemaError = null
    }

    loadSchema()

    return { state, isLoggedIn, onLogin, onLogout }
  },
  template: `
    <login-form v-if="!isLoggedIn" @login="onLogin" />
    <div v-else-if="!state.schema && !state.schemaError" style="padding:2rem;text-align:center">
      <span class="spinner"></span> Loading schema…
    </div>
    <div v-else-if="state.schemaError" class="error-banner" style="margin:2rem">
      Failed to load schema: {{ state.schemaError }}
    </div>
    <entity-editor v-else :schema="state.schema" @logout="onLogout" />
  `
}

createApp(App).mount('#app')
