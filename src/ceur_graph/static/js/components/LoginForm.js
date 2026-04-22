export default {
  name: 'LoginForm',
  emits: ['login'],
  setup(_, { emit }) {
    const { ref } = Vue

    const username = ref('')
    const password = ref('')
    const error = ref('')
    const loading = ref(false)

    async function submit() {
      error.value = ''
      loading.value = true
      try {
        const body = new URLSearchParams({ username: username.value, password: password.value })
        const resp = await fetch('/token', { method: 'POST', body })
        if (!resp.ok) {
          error.value = 'Invalid credentials'
          return
        }
        const data = await resp.json()
        localStorage.setItem('token', data.access_token)
        emit('login', data.access_token)
      } catch (e) {
        error.value = e.message
      } finally {
        loading.value = false
      }
    }

    return { username, password, error, loading, submit }
  },
  template: `
    <main class="container">
      <article style="max-width:380px;margin:4rem auto;">
        <hgroup>
          <h2>CEUR-WS Entity Editor</h2>
          <p>Sign in with your Wikibase bot credentials</p>
        </hgroup>
        <div v-if="error" class="error-banner">{{ error }}</div>
        <form @submit.prevent="submit">
          <label>Username <input v-model="username" type="text" autocomplete="username" required /></label>
          <label>Password <input v-model="password" type="password" autocomplete="current-password" required /></label>
          <button type="submit" :aria-busy="loading">Sign in</button>
        </form>
      </article>
    </main>
  `
}
