import { LANGUAGES, useI18n } from "../i18n.js";

export default {
  name: "LoginForm",
  setup() {
    const { ref } = Vue;
    const { t, locale, setLocale } = useI18n();

    const error = ref("");
    const loading = ref(false);

    function loginWithWikibase() {
      error.value = "";
      loading.value = true;
      window.location.href = "/oauth/login";
    }

    return {
      error,
      loading,
      loginWithWikibase,
      t,
      locale,
      setLocale,
      LANGUAGES,
    };
  },
  template: `
    <main class="login-page">
      <article class="login-card">
        <hgroup>
          <h2>{{ t('login_title') }}</h2>
          <p>{{ t('login_subtitle') }}</p>
        </hgroup>
        <div v-if="error" class="error-banner">{{ error }}</div>
        <button type="button" :aria-busy="loading" @click="loginWithWikibase">
          {{ t('login_submit') }}
        </button>
        <div class="login-lang">
          <select :value="locale" @change="setLocale($event.target.value)">
            <option v-for="(label, code) in LANGUAGES" :key="code" :value="code">{{ label }}</option>
          </select>
        </div>
      </article>
    </main>
  `,
};
