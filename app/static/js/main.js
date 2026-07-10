// NovaShop ERP — comportamiento global de la interfaz (sidebar, topbar)
document.addEventListener("DOMContentLoaded", function () {
  // CSRF token global para todas las peticiones AJAX POST
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = csrfMeta ? csrfMeta.getAttribute("content") : "";

  // Interceptar fetch para añadir CSRF header en POST/PUT/DELETE
  const originalFetch = window.fetch;
  window.fetch = function (url, opts) {
    opts = opts || {};
    const method = (opts.method || "GET").toUpperCase();
    if (csrfToken && ["POST", "PUT", "DELETE", "PATCH"].includes(method)) {
      opts.headers = opts.headers || {};
      if (opts.headers instanceof Headers) {
        if (!opts.headers.has("X-CSRFToken")) {
          opts.headers.set("X-CSRFToken", csrfToken);
        }
      } else {
        opts.headers["X-CSRFToken"] = opts.headers["X-CSRFToken"] || csrfToken;
      }
    }
    return originalFetch.call(this, url, opts);
  };

  const sidebar = document.getElementById("nsSidebar");
  const main = document.getElementById("nsMain");
  const overlay = document.getElementById("nsOverlay");
  const btnCollapse = document.getElementById("nsBtnCollapse");
  const btnMobileToggle = document.getElementById("nsBtnMobileToggle");

  // Colapsar/expandir sidebar en escritorio, con persistencia en sesión
  const COLLAPSE_KEY = "ns_sidebar_collapsed";
  if (sessionStorage === undefined) {
    // noop — algunos entornos de preview bloquean storage; degradamos con calma
  }

  function applyCollapsedState(collapsed) {
    sidebar.classList.toggle("is-collapsed", collapsed);
    main.classList.toggle("is-collapsed", collapsed);
  }

  try {
    const saved = window.sessionStorage.getItem(COLLAPSE_KEY);
    if (saved === "1") applyCollapsedState(true);
  } catch (e) {
    /* almacenamiento no disponible: se ignora silenciosamente */
  }

  if (btnCollapse) {
    btnCollapse.addEventListener("click", function () {
      const collapsed = !sidebar.classList.contains("is-collapsed");
      applyCollapsedState(collapsed);
      try {
        window.sessionStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "0");
      } catch (e) {}
    });
  }

  // Sidebar en móvil (drawer)
  function toggleMobileSidebar(open) {
    sidebar.classList.toggle("is-mobile-open", open);
    overlay.classList.toggle("is-visible", open);
  }

  if (btnMobileToggle) {
    btnMobileToggle.addEventListener("click", () => toggleMobileSidebar(true));
  }
  if (overlay) {
    overlay.addEventListener("click", () => toggleMobileSidebar(false));
  }

  // Mover todos los modales a document.body para evitar stacking contexts
  document.querySelectorAll(".modal").forEach(function (modal) {
    if (modal.parentElement !== document.body) {
      document.body.appendChild(modal);
    }
  });

  // Inicializar tooltips de Bootstrap si existen
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggerList.forEach((el) => new bootstrap.Tooltip(el));
});

// Helper reutilizable para confirmaciones destructivas con SweetAlert2
function nsConfirmarEliminacion(mensaje) {
  return Swal.fire({
    title: "¿Confirmar eliminación?",
    text: mensaje || "Esta acción no se puede deshacer.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#e5484d",
    cancelButtonColor: "#6b7280",
    reverseButtons: true,
  });
}
