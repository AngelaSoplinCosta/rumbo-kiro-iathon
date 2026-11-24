// Sesion simulada y guard de paginas. Todo en localStorage (prototipo).

const AUTH = {
  USUARIO_OK: "demo",
  CLAVE_OK: "demo01",

  entrar(usuario, clave) {
    if (usuario === this.USUARIO_OK && clave === this.CLAVE_OK) {
      localStorage.setItem("rumbo_sesion", "1");
      return true;
    }
    return false;
  },

  salir() {
    localStorage.removeItem("rumbo_sesion");
    window.location.href = "login.html";
  },

  haySesion() {
    return localStorage.getItem("rumbo_sesion") === "1";
  },

  configuro() {
    return localStorage.getItem("rumbo_onboarding") === "1";
  },

  marcarConfigurado() {
    localStorage.setItem("rumbo_onboarding", "1");
  },

  // Protege una pagina del app. Llamar al inicio de cada pantalla interna.
  // 1) sin sesion -> login. 2) con sesion pero sin configurar -> onboarding.
  proteger() {
    if (!this.haySesion()) {
      window.location.replace("login.html");
      return false;
    }
    if (!this.configuro()) {
      window.location.replace("onboarding.html");
      return false;
    }
    return true;
  },
};
