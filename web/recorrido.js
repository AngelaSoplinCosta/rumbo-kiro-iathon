/* Recorrido demostrativo: las preguntas y contenidos son ejemplos locales. */
(() => {
  const labels = ["Tu objetivo", "Tu ruta", "Practica", "Tu avance"];
  const state = { step: 0, goal: "", answer: "", checked: false };
  const view = document.querySelector("#view");
  const steps = document.querySelector("#steps");
  const mobile = document.querySelector("#mobile-progress");
  const intro = (eyebrow, title, copy) => `<div class="intro"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${copy}</p></div><div class="tutor"><img src="mascota.svg" alt="Conejito tutor con birrete"><span class="tutor-caption">Tu tutor de estudio ✦</span></div></div>`;
  function render() {
    steps.innerHTML = labels.map((label, i) => `<li class="${i === state.step ? "active" : i < state.step ? "done" : ""}" ${i === state.step ? 'aria-current="step"' : ""}><span class="num">${i < state.step ? "✓" : i + 1}</span>${label}</li>`).join("");
    mobile.textContent = `PASO ${state.step + 1} DE 4 · ${labels[state.step].toUpperCase()}`;
    if (state.step === 0) {
      view.innerHTML = intro("Hola, qué bueno verte por aquí", "Aprender puede ser<br><em>más ligero.</em>", "Te acompaño a descubrir una forma sencilla de avanzar. Empecemos con un ejemplo, un paso a la vez.") + `<div class="panel"><div class="panel-head"><div><h2>¿Qué te gustaría hacer hoy?</h2><p class="muted">Elige un objetivo para comenzar este recorrido de ejemplo.</p></div><span class="pill">✦ PASO 01</span></div><div class="choice-grid" role="group" aria-label="Objetivo de estudio">
        <button class="choice" type="button" data-goal="repasar" aria-pressed="${state.goal === "repasar"}"><span class="emoji">📚</span><span><strong>Repasar un tema</strong><small>Recordar lo que ya aprendí</small></span></button>
        <button class="choice" type="button" data-goal="examen" aria-pressed="${state.goal === "examen"}"><span class="emoji">🎯</span><span><strong>Preparar un examen</strong><small>Organizar mis próximos pasos</small></span></button>
        <button class="choice" type="button" data-goal="empezar" aria-pressed="${state.goal === "empezar"}"><span class="emoji">🌱</span><span><strong>Empezar de cero</strong><small>Aprender con calma</small></span></button></div>
        <div class="hint"><span>✿</span><span>Esta es una experiencia con contenido ficticio. Aquí no se cargan documentos ni se genera una ruta con IA.</span></div><p class="error" id="error" role="alert"></p><div class="actions"><span class="muted">Puedes cambiar tu elección después.</span><button class="button" data-action="next">Ver mi ruta de ejemplo →</button></div></div>`;
    } else if (state.step === 1) {
      view.innerHTML = intro("Una ruta a tu ritmo", "Un pequeño plan,<br><em>un gran comienzo.</em>", "Esta ruta de ejemplo te muestra cómo podrías organizar una sesión corta de estudio.") + `<div class="panel"><div class="panel-head"><div><h2>Tu ruta de ejemplo</h2><p class="muted">Tema ficticio: cómo estudiar en pequeños pasos.</p></div><span class="pill">✦ PASO 02</span></div><div class="road"><div class="road-item"><span class="bubble">📖</span><div><strong>Conoce la idea</strong><small>Una meta concreta hace más fácil empezar.</small></div><span class="duration">2 min</span></div><div class="road-item"><span class="bubble">✏️</span><div><strong>Practica</strong><small>Responde una pregunta breve.</small></div><span class="duration">1 min</span></div><div class="road-item"><span class="bubble">🌟</span><div><strong>Reconoce tu avance</strong><small>Celebra haber dado el primer paso.</small></div><span class="duration">1 min</span></div></div><div class="hint"><span>✿</span><span>La ruta es un ejemplo fijo: todavía no se adapta al objetivo que elegiste ni usa tus documentos.</span></div><div class="actions"><button class="text-button" data-action="back">← Cambiar objetivo</button><button class="button" data-action="next">Empezar práctica →</button></div></div>`;
    } else if (state.step === 2) {
      view.innerHTML = intro("Un momento para practicar", "Lo estás haciendo<br><em>muy bien.</em>", "No necesitas hacerlo perfecto. Lee la pregunta y elige la respuesta que más sentido tenga para ti.") + `<div class="panel"><div class="panel-head"><div><h2>Una pregunta para empezar</h2><p class="muted">Basada en el contenido de ejemplo del paso anterior.</p></div><span class="pill">✦ PASO 03</span></div><p><strong>¿Qué puede ayudarte a empezar a estudiar?</strong></p><div class="quiz">
        <label><input type="radio" name="answer" value="a" ${state.answer === "a" ? "checked" : ""}> Esperar hasta tener todo el día libre.</label>
        <label><input type="radio" name="answer" value="b" ${state.answer === "b" ? "checked" : ""}> Elegir una meta pequeña y concreta.</label>
        <label><input type="radio" name="answer" value="c" ${state.answer === "c" ? "checked" : ""}> Intentar aprender todo de una vez.</label></div>
        <div id="feedback" aria-live="polite"></div><p class="error" id="error" role="alert"></p><div class="actions"><button class="text-button" data-action="back">← Volver a la ruta</button><button class="button" data-action="check">Revisar respuesta →</button></div></div>`;
      if (state.checked) showFeedback();
    } else {
      view.innerHTML = intro("¡Una pequeña victoria!", "Cada paso<br><em>cuenta.</em>", "Hoy hiciste espacio para aprender. Puedes volver a empezar cuando lo necesites.") + `<div class="panel celebrate"><div class="big">🌟</div><h2>¡Terminaste la práctica!</h2><p class="muted">Completaste el recorrido de ejemplo. Celebremos tu primer paso.</p><div class="hint"><span>✿</span><span>Este avance es una demostración y no se guarda en una cuenta. La ruta con documentos propios requiere integración y validación adicionales.</span></div><div class="actions"><button class="button secondary" data-action="restart">Volver a empezar</button><a class="button" href="login.html">Volver al inicio →</a></div></div>`;
    }
  }
  function showFeedback() {
    const correct = state.answer === "b";
    document.querySelector("#feedback").innerHTML = correct
      ? '<div class="feedback"><strong>¡Exacto! ✨</strong> Una meta pequeña y concreta puede ayudarte a comenzar sin sentir tanta presión.</div>'
      : '<div class="feedback retry"><strong>Buen intento 💛</strong> Prueba otra vez: piensa en una acción pequeña y alcanzable.</div>';
    if (correct) document.querySelector('[data-action="check"]').textContent = "Continuar →";
  }
  view.addEventListener("click", (event) => {
    const goal = event.target.closest("[data-goal]");
    if (goal) {
      state.goal = goal.dataset.goal;
      document.querySelectorAll("[data-goal]").forEach(button => button.setAttribute("aria-pressed", String(button === goal)));
      document.querySelector("#error").textContent = "";
      return;
    }
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (!action) return;
    if (action === "next") {
      if (state.step === 0 && !state.goal) { document.querySelector("#error").textContent = "Elige una opción para continuar."; return; }
      state.step++;
    } else if (action === "back") { state.step--; }
    else if (action === "restart") { state.step = 0; state.goal = ""; state.answer = ""; state.checked = false; }
    else if (action === "check") {
      const selected = document.querySelector('input[name="answer"]:checked');
      if (!selected) { document.querySelector("#error").textContent = "Elige una respuesta para continuar."; return; }
      state.answer = selected.value;
      if (state.checked && state.answer === "b") { state.step++; }
      else { state.checked = true; document.querySelector("#error").textContent = ""; showFeedback(); return; }
    }
    render();
    view.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  });
  view.addEventListener("change", (event) => {
    if (event.target.name === "answer") {
      state.answer = event.target.value;
      state.checked = false;
      document.querySelector("#feedback").innerHTML = "";
      document.querySelector("#error").textContent = "";
      document.querySelector('[data-action="check"]').textContent = "Revisar respuesta →";
    }
  });
  render();
})();
