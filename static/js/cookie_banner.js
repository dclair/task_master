(() => {
  const STORAGE_KEY = "tm_cookie_consent_v1";
  const COOKIE_API_URL = "/accounts/cookie-consent/";
  const OPTIONAL_COOKIE = "_tm_optional";
  const SESSION_COOKIE = "sessionid";
  const CSRF_COOKIE = "csrftoken";

  const banner = document.getElementById("cookie-banner");
  if (!banner) return;

  const note = document.getElementById("cookie-banner-note");
  const isAuthenticated = document.body.dataset.authenticated === "true";

  const setCookie = (name, value, days) => {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
  };

  const deleteCookie = (name) => {
    document.cookie = `${name}=; Max-Age=0; path=/; SameSite=Lax`;
  };

  const rememberChoice = (choice) => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ choice, at: new Date().toISOString() })
    );
  };

  const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === `${name}=`) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };

  const syncChoiceToBackend = async (choice) => {
    if (!isAuthenticated) return;
    const csrf = getCookie(CSRF_COOKIE);
    if (!csrf) return;

    await fetch(COOKIE_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf,
      },
      body: JSON.stringify({ choice }),
      credentials: "same-origin",
    });
  };

  const loadChoiceFromBackend = async () => {
    if (!isAuthenticated) return null;
    try {
      const response = await fetch(COOKIE_API_URL, { credentials: "same-origin" });
      if (!response.ok) return null;
      const data = await response.json();
      return data && data.choice ? data.choice : null;
    } catch {
      return null;
    }
  };

  const applyChoice = (choice) => {
    if (choice === "all") {
      setCookie(OPTIONAL_COOKIE, "1", 180);
      deleteCookie("_ga");
      if (note) {
        note.classList.add("d-none");
      }
      return;
    }

    if (choice === "essential") {
      deleteCookie(OPTIONAL_COOKIE);
      deleteCookie("_ga");
      if (note) {
        note.classList.add("d-none");
      }
      return;
    }

    // reject: intentamos minimizar persistencia eliminando cookies opcionales y de sesión.
    deleteCookie(OPTIONAL_COOKIE);
    deleteCookie("_ga");
    deleteCookie(CSRF_COOKIE);
    deleteCookie(SESSION_COOKIE);

    if (note) {
      note.textContent =
        "Has rechazado todas las cookies. Algunas funciones de acceso y formularios pueden quedar deshabilitadas.";
      note.classList.remove("d-none");
    }

    if (isAuthenticated) {
      const logoutForm = document.querySelector('form[action*="/accounts/logout"]');
      if (logoutForm) {
        // Cerramos sesión para aplicar la elección de no mantener cookies de sesión.
        setTimeout(() => logoutForm.submit(), 900);
      }
    }
  };

  const hideBanner = () => banner.classList.add("d-none");
  const showBanner = () => banner.classList.remove("d-none");

  const initBanner = async () => {
    if (isAuthenticated) {
      const backendChoice = await loadChoiceFromBackend();
      if (backendChoice) {
        rememberChoice(backendChoice);
        hideBanner();
        return;
      }
    }

    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      hideBanner();
      return;
    }

    showBanner();
  };

  banner.querySelectorAll("[data-cookie-choice]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const choice = btn.getAttribute("data-cookie-choice");
      rememberChoice(choice);
      await syncChoiceToBackend(choice);
      applyChoice(choice);

      // Damos tiempo a mostrar nota en rechazo antes de ocultar (si no hay logout).
      if (choice === "reject" && !isAuthenticated) {
        setTimeout(hideBanner, 1200);
      } else if (choice !== "reject") {
        hideBanner();
      }
    });
  });

  initBanner();
})();
