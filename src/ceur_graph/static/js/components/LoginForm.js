import { LANGUAGES, useI18n } from "../i18n.js";

export default {
  name: "LoginForm",
  emits: ["login"],
  setup(_, { emit }) {
    const { ref } = Vue;
    const { t, locale, setLocale } = useI18n();

    const username = ref("");
    const password = ref("");
    const error = ref("");
    const loading = ref(false);

    async function submit() {
      error.value = "";
      loading.value = true;
      try {
        const body = new URLSearchParams({
          username: username.value,
          password: password.value,
        });
        const resp = await fetch("/token", { method: "POST", body });
        if (!resp.ok) {
          error.value = t("login_invalid");
          return;
        }
        const data = await resp.json();
        localStorage.setItem("token", data.access_token);
        emit("login", data.access_token);
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    }

    return {
      username,
      password,
      error,
      loading,
      submit,
      t,
      locale,
      setLocale,
      LANGUAGES,
    };
  },
  template: `
    <main class="container">
      <article style="max-width:380px;margin:4rem auto;">
        <hgroup>
          <h2>{{ t('login_title') }}</h2>
          <p>{{ t('login_subtitle') }}</p>
        </hgroup>
        <div v-if="error" class="error-banner">{{ error }}</div>
        <form @submit.prevent="submit">
          <label>{{ t('login_username') }} <input v-model="username" type="text" autocomplete="username" required /></label>
          <label>{{ t('login_password') }} <input v-model="password" type="password" autocomplete="current-password" required /></label>
          <button type="submit" :aria-busy="loading">{{ t('login_submit') }}</button>
        </form>
        <div style="text-align:center;margin-top:1rem">
          <select :value="locale" @change="setLocale($event.target.value)" style="width:auto;display:inline-block">
            <option v-for="(label, code) in LANGUAGES" :key="code" :value="code">{{ label }}</option>
          </select>
        </div>
      </article>
    </main>
  `,
};
