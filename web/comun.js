// Shell de la app: barra lateral, panel derecho y utilidades. Datos simulados.

const USUARIO = { nombre: "Lucía", inicial: "L", correo: "lucia@example.com", rol: "Estudiante" };

// Barra lateral izquierda. `activo` resalta la seccion.
function barraLateral(activo) {
  const nav = [
    { s: "hoy", h: "index.html", i: "🏠", t: "Hoy" },
    { s: "espacios", h: "espacios.html", i: "📚", t: "Espacios" },
    { s: "calendario", h: "calendario.html", i: "📅", t: "Calendario" },
    { s: "progreso", h: "progreso.html", i: "📈", t: "Progreso" },
    { s: "amigos", h: "amigos.html", i: "👥", t: "Amigos" },
  ];
  // Solo accesos fijos: subir, el espacio Demo y el panel de demo.
  // Los cursos reales se listan en la pantalla Espacios (desde la API).
  const cursos = [
    { h: "subir.html", i: "⬆️", t: "Subir PDFs" },
    { h: "espacio.html?demo=1", i: "🎃", t: "Demo" },
    { h: "demo.html", i: "🎬", t: "Panel de demo" },
  ];
  return `
  <aside class="lateral" id="lateral">
    <div class="marca">Rumbo <span class="punto">🎓</span></div>
    ${nav.map((n) => `<a class="nav-item ${n.s === activo ? "activo" : ""}" href="${n.h}"><span class="ico">${n.i}</span>${n.t}</a>`).join("")}
    <div class="nav-sec">Mis espacios</div>
    ${cursos.map((c) => `<a class="nav-item" href="${c.h}"><span class="ico">${c.i}</span>${c.t}</a>`).join("")}
    <div class="pie">
      <a class="avatar sm" href="perfil.html">${USUARIO.inicial}</a>
      <div class="info"><b>${USUARIO.nombre}</b><small>${USUARIO.correo}</small></div>
      <button class="salir" title="Cerrar sesión" onclick="AUTH.salir()">⎋</button>
    </div>
  </aside>
  <div class="velo" id="velo" onclick="cerrarMenu()"></div>`;
}

// Panel derecho tipo "perfil" (como la referencia). Opcional por pantalla.
function panelDerecho(extra) {
  return `
  <aside class="derecho">
    <div class="perfil-cab">
      <a class="avatar lg" href="perfil.html">${USUARIO.inicial}</a>
      <div class="nombre"><b>${USUARIO.nombre}</b><small>Resolviendo problemas</small></div>
    </div>
    <div class="bloque-d">
      <div class="et">Mi meta</div>
      <p style="font-size:0.92rem">Quiero <b>llegar lista al parcial de Física I</b> dominando lo esencial.</p>
    </div>
    <div class="bloque-d">
      <div class="et">Cómo me gusta aprender</div>
      <div class="pref"><div class="flex"><span>Viendo y dibujando</span></div><div class="minibar"><span style="width:80%;background:var(--marca)"></span></div></div>
      <div class="pref"><div class="flex"><span>Leyendo y escribiendo</span></div><div class="minibar"><span style="width:55%;background:#8b5cf6"></span></div></div>
      <div class="pref"><div class="flex"><span>Escuchando</span></div><div class="minibar"><span style="width:35%;background:var(--alerta)"></span></div></div>
    </div>
    <div class="bloque-d">
      <div class="et">Valores</div>
      <div class="valores">
        <span class="valor">🌱 Constancia</span><span class="valor">💡 Curiosidad</span>
        <span class="valor">🎯 Enfoque</span><span class="valor">🤝 Apoyo</span>
      </div>
    </div>
    <div class="bloque-d">
      <div class="et">Sesiones de estudio</div>
      <p style="font-size:0.85rem;color:var(--texto-suave);margin-bottom:10px">174 sesiones en el último año</p>
      <div class="heat" id="heat"></div>
      <div class="leyenda"><span>Menos</span><i></i><i class="l1"></i><i class="l2"></i><i class="l3"></i><i class="l4"></i><span>Más</span></div>
    </div>
    ${extra || ""}
  </aside>`;
}

// Monta el shell completo. `op = { activo, derecho, centro }`.
function montarApp(op) {
  const html =
    '<div class="layout">' +
    barraLateral(op.activo) +
    '<main class="centro">' +
    '<button class="menu-movil" onclick="abrirMenu()">☰ Menú</button>' +
    op.centro +
    "</main>" +
    (op.derecho === false ? "" : panelDerecho(op.derechoExtra)) +
    "</div>";
  document.getElementById("app").innerHTML = html;
  pintarHeat();
}

function pintarHeat() {
  const h = document.getElementById("heat");
  if (!h) return;
  const clases = ["", "", "l1", "l1", "l2", "l2", "l3", "l4"];
  let s = "";
  for (let i = 0; i < 70; i++) s += `<i class="${clases[Math.floor(Math.random() * clases.length)]}"></i>`;
  h.innerHTML = s;
}

function abrirMenu() { document.getElementById("lateral").classList.add("abierta"); document.getElementById("velo").classList.add("ver"); }
function cerrarMenu() { document.getElementById("lateral").classList.remove("abierta"); document.getElementById("velo").classList.remove("ver"); }

function toast(texto) {
  let t = document.querySelector(".toast");
  if (!t) { t = document.createElement("div"); t.className = "toast"; document.body.appendChild(t); }
  t.textContent = texto;
  requestAnimationFrame(() => t.classList.add("ver"));
  clearTimeout(t._tmr);
  t._tmr = setTimeout(() => t.classList.remove("ver"), 2600);
}

// Modal simple: abrir/cerrar por id.
function abrirModal(id) { document.getElementById(id).classList.add("ver"); }
function cerrarModal(id) { document.getElementById(id).classList.remove("ver"); }

const DEMO = {
  temas: [
    { nombre: "Cinemática", estado: "completado", dia: "Día 1" },
    { nombre: "Movimiento 2D", estado: "completado", dia: "Día 2" },
    { nombre: "Leyes de Newton", estado: "encurso", dia: "Hoy" },
    { nombre: "Dinámica", estado: "bloqueado", dia: "Día 4" },
    { nombre: "Trabajo y energía", estado: "bloqueado", dia: "Día 5" },
    { nombre: "Simulacro final", estado: "bloqueado", dia: "Día 6", tipo: "simulacro" },
    { nombre: "Examen", estado: "examen", dia: "5 nov", tipo: "examen" },
  ],
};
