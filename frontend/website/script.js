// Mobile nav toggle
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector(".menu-toggle");
  const navList = document.querySelector("nav ul");

  if (toggle && navList) {
    toggle.addEventListener("click", () => {
      navList.classList.toggle("open");
    });
  }

  // Highlight active nav link based on current page
  const currentPage = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll("nav a").forEach((link) => {
    const href = link.getAttribute("href");
    if (href === currentPage) {
      link.classList.add("active");
    }
  });

  // Contact form handling (client-side only, no backend configured)
  const form = document.getElementById("contact-form");
  const status = document.getElementById("form-status");

  if (form && status) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      status.style.display = "block";
      status.textContent = "Thanks! Your message has been noted (demo form, no backend wired up).";
      form.reset();
    });
  }
});

// ---------------------------------------------------------------------
// DevOpsHub backend integration (appended -- everything above this line
// is the original nav/contact-form logic, unchanged).
// ---------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const api = window.DevOpsHubAPI;
  if (!api) return; // api.js not loaded on this page

  renderAuthWidget(api);
  wireArticleList(api);
  wireLatestPosts(api);
  wireArticleDetail(api);
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

function articleCardHtml(article, categoryName) {
  const tag = categoryName || "General";
  const summary = article.summary || article.content.slice(0, 140) + "...";
  return `
    <article class="card">
      <span class="tag">${escapeHtml(tag)}</span>
      <h3><a href="blog.html?article=${article.id}">${escapeHtml(article.title)}</a></h3>
      <p>${escapeHtml(summary)}</p>
    </article>
  `;
}

async function categoryLookup(api) {
  try {
    const cats = await api.listCategories();
    const map = {};
    cats.items.forEach((c) => (map[c.id] = c.name));
    return map;
  } catch (_) {
    return {};
  }
}

// --- Home page: "Latest Posts" grid -----------------------------------
function wireLatestPosts(api) {
  const grid = document.getElementById("latest-posts-grid");
  if (!grid) return;

  Promise.all([api.listArticles({ page: 1, page_size: 6 }), categoryLookup(api)])
    .then(([data, catMap]) => {
      if (!data.items.length) return; // keep existing static fallback cards
      grid.innerHTML = data.items
        .map((a) => articleCardHtml(a, catMap[a.category_id]))
        .join("");
    })
    .catch(() => {
      // Backend unreachable -- leave the existing static cards in place.
    });
}

// --- Blog page: full searchable/filterable list + pagination ----------
function wireArticleList(api) {
  const grid = document.getElementById("dynamic-articles-grid");
  if (!grid) return;

  // If a specific article is requested via ?article=, the detail view
  // (wireArticleDetail) takes over and this grid stays hidden.
  const params = new URLSearchParams(window.location.search);
  if (params.get("article")) return;

  const searchInput = document.getElementById("search-input");
  const categorySelect = document.getElementById("category-filter");
  let currentPage = 1;
  const pageSize = 9;
  let categoriesById = {};

  async function load() {
    const query = {};
    if (searchInput && searchInput.value.trim()) query.q = searchInput.value.trim();
    if (categorySelect && categorySelect.value) query.category_id = categorySelect.value;
    query.page = currentPage;
    query.page_size = pageSize;

    try {
      const data = await api.listArticles(query);
      if (!data.items.length) {
        grid.innerHTML = `<p>No articles found${query.q ? ` for "${escapeHtml(query.q)}"` : ""}.</p>`;
        return;
      }
      grid.innerHTML = data.items
        .map((a) => articleCardHtml(a, categoriesById[a.category_id]))
        .join("");
    } catch (err) {
      grid.innerHTML = `<p>Could not load articles from the API (${escapeHtml(err.message)}). Showing nothing dynamic -- backend may be offline.</p>`;
    }
  }

  api
    .listCategories()
    .then((cats) => {
      cats.items.forEach((c) => (categoriesById[c.id] = c.name));
      if (categorySelect) {
        cats.items.forEach((c) => {
          const opt = document.createElement("option");
          opt.value = c.id;
          opt.textContent = c.name;
          categorySelect.appendChild(opt);
        });
      }
    })
    .catch(() => {})
    .finally(load);

  if (searchInput) {
    let debounce;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        currentPage = 1;
        load();
      }, 300);
    });
  }
  if (categorySelect) {
    categorySelect.addEventListener("change", () => {
      currentPage = 1;
      load();
    });
  }
}

// --- Blog page: single-article detail view (?article=<id>) ------------
function wireArticleDetail(api) {
  const detailEl = document.getElementById("article-detail");
  if (!detailEl) return;

  const params = new URLSearchParams(window.location.search);
  const articleId = params.get("article");
  if (!articleId) return;

  const grid = document.getElementById("dynamic-articles-grid");
  const heading = document.querySelector("main h2");
  if (grid) grid.style.display = "none";
  if (heading) heading.style.display = "none";

  detailEl.style.display = "block";
  detailEl.innerHTML = "<p>Loading article...</p>";

  api
    .getArticle(articleId)
    .then((article) => {
      detailEl.innerHTML = `
        <a class="btn btn-outline" href="blog.html">&larr; Back to all posts</a>
        <h2>${escapeHtml(article.title)}</h2>
        <p>${escapeHtml(article.content)}</p>
      `;
    })
    .catch((err) => {
      detailEl.innerHTML = `
        <a class="btn btn-outline" href="blog.html">&larr; Back to all posts</a>
        <p>Could not load this article (${escapeHtml(err.message)}).</p>
      `;
    });
}

// --- Auth widget + notifications bell (all pages) ----------------------
function renderAuthWidget(api) {
  const navbar = document.querySelector(".navbar");
  if (!navbar || document.querySelector(".nav-auth")) return;

  const container = document.createElement("div");
  container.className = "nav-auth";
  navbar.appendChild(container);

  const backdrop = document.createElement("div");
  backdrop.className = "auth-modal-backdrop";
  backdrop.innerHTML = `
    <div class="auth-modal">
      <h3 id="auth-modal-title">Log In</h3>
      <div class="form-group">
        <label for="auth-email">Email</label>
        <input type="email" id="auth-email" />
      </div>
      <div class="form-group" id="auth-username-group" style="display:none;">
        <label for="auth-username">Username</label>
        <input type="text" id="auth-username" />
      </div>
      <div class="form-group">
        <label for="auth-password">Password</label>
        <input type="password" id="auth-password" />
      </div>
      <p class="auth-error" id="auth-error"></p>
      <button class="btn" id="auth-submit">Log In</button>
      <button class="btn btn-outline" id="auth-cancel" type="button">Cancel</button>
      <p class="auth-switch">
        <a id="auth-switch-link">Need an account? Register</a>
      </p>
    </div>
  `;
  document.body.appendChild(backdrop);

  let mode = "login"; // or "register"

  function closeModal() {
    backdrop.classList.remove("open");
    document.getElementById("auth-error").textContent = "";
  }

  function openModal(newMode) {
    mode = newMode;
    document.getElementById("auth-modal-title").textContent = mode === "login" ? "Log In" : "Register";
    document.getElementById("auth-submit").textContent = mode === "login" ? "Log In" : "Register";
    document.getElementById("auth-username-group").style.display = mode === "register" ? "block" : "none";
    document.getElementById("auth-switch-link").textContent =
      mode === "login" ? "Need an account? Register" : "Already have an account? Log in";
    backdrop.classList.add("open");
  }

  document.getElementById("auth-cancel").addEventListener("click", closeModal);
  document.getElementById("auth-switch-link").addEventListener("click", () => {
    openModal(mode === "login" ? "register" : "login");
  });
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) closeModal();
  });

  document.getElementById("auth-submit").addEventListener("click", async () => {
    const email = document.getElementById("auth-email").value.trim();
    const password = document.getElementById("auth-password").value;
    const errorEl = document.getElementById("auth-error");
    errorEl.textContent = "";

    try {
      if (mode === "login") {
        await api.login(email, password);
      } else {
        const username = document.getElementById("auth-username").value.trim();
        await api.register(email, username, password);
      }
      closeModal();
      renderNavState();
    } catch (err) {
      errorEl.textContent = err.message;
    }
  });

  function renderNavState() {
    container.innerHTML = "";
    const user = api.getUser();

    if (!user) {
      const loginBtn = document.createElement("button");
      loginBtn.className = "btn btn-outline";
      loginBtn.textContent = "Log In";
      loginBtn.addEventListener("click", () => openModal("login"));
      container.appendChild(loginBtn);
      return;
    }

    const bell = document.createElement("button");
    bell.className = "notif-bell";
    bell.textContent = "\uD83D\uDD14";
    const badge = document.createElement("span");
    badge.className = "notif-badge";
    badge.style.display = "none";
    bell.appendChild(badge);

    const dropdown = document.createElement("div");
    dropdown.className = "notif-dropdown";
    dropdown.innerHTML = "<p>Loading...</p>";

    bell.addEventListener("click", () => {
      dropdown.classList.toggle("open");
    });

    api
      .listNotifications()
      .then((data) => {
        if (data.unread_count > 0) {
          badge.textContent = data.unread_count;
          badge.style.display = "inline-block";
        }
        if (!data.items.length) {
          dropdown.innerHTML = "<p>No notifications yet.</p>";
          return;
        }
        dropdown.innerHTML = "";
        data.items.forEach((n) => {
          const item = document.createElement("div");
          item.className = "notif-item" + (n.is_read ? "" : " unread");
          item.textContent = n.message;
          item.addEventListener("click", () => {
            if (!n.is_read) {
              api.markNotificationRead(n.id).then(() => {
                item.classList.remove("unread");
                const remaining = data.items.filter((x) => !x.is_read && x.id !== n.id).length;
                if (remaining > 0) {
                  badge.textContent = remaining;
                } else {
                  badge.style.display = "none";
                }
              });
            }
          });
          dropdown.appendChild(item);
        });
      })
      .catch(() => {
        dropdown.innerHTML = "<p>Could not load notifications.</p>";
      });

    const wrapper = document.createElement("div");
    wrapper.style.position = "relative";
    wrapper.appendChild(bell);
    wrapper.appendChild(dropdown);
    container.appendChild(wrapper);

    const logoutBtn = document.createElement("button");
    logoutBtn.className = "btn btn-outline";
    logoutBtn.textContent = `Log Out (${user.username})`;
    logoutBtn.addEventListener("click", () => {
      api.logout();
      renderNavState();
    });
    container.appendChild(logoutBtn);
  }

  renderNavState();
}
