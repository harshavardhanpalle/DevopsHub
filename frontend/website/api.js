// DevOpsHub API client.
//
// The browser only ever talks to same-origin `/api/...` paths -- the
// frontend's own nginx.conf reverse-proxies those to the gateway container,
// which fans out to the right microservice. No CORS configuration is
// needed on the frontend because of this.
(function () {
  const TOKEN_KEY = "devopshub_token";
  const USER_KEY = "devopshub_user";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function getUser() {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  async function apiFetch(path, options = {}) {
    const headers = Object.assign({}, options.headers || {});
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    if (options.body) headers["Content-Type"] = "application/json";

    const resp = await fetch(path, Object.assign({}, options, { headers }));
    if (!resp.ok) {
      let detail = `Request failed (${resp.status})`;
      try {
        const data = await resp.json();
        detail = data.detail || detail;
      } catch (_) {
        /* ignore parse errors */
      }
      throw new Error(detail);
    }
    if (resp.status === 204) return null;
    return resp.json();
  }

  const api = {
    getToken,
    getUser,
    clearSession,

    register(email, username, password) {
      return apiFetch("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, username, password }),
      }).then((data) => {
        setSession(data.access_token, data.user);
        return data;
      });
    },

    login(email, password) {
      return apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }).then((data) => {
        setSession(data.access_token, data.user);
        return data;
      });
    },

    logout() {
      clearSession();
    },

    listArticles(params = {}) {
      const qs = new URLSearchParams(params).toString();
      return apiFetch(`/api/articles${qs ? "?" + qs : ""}`);
    },

    getArticle(id) {
      return apiFetch(`/api/articles/${id}`);
    },

    listCategories() {
      return apiFetch("/api/categories");
    },

    listNotifications() {
      return apiFetch("/api/notifications");
    },

    markNotificationRead(id) {
      return apiFetch(`/api/notifications/${id}/read`, { method: "POST" });
    },
  };

  window.DevOpsHubAPI = api;
})();
