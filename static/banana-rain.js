/* Banana Rain – falling bananas background (adapted from CodePen createjs/qQeXee)
 * Vanilla Canvas2D – no dependencies.
 * Renders behind all content via a fixed canvas at z-index:-1.
 */
(function () {
  "use strict";

  var canvas = document.getElementById("banana-rain");
  if (!canvas) return;
  var ctx = canvas.getContext("2d");

  // ── Config ──────────────────────────────────────────
  var MAX_BANANAS = 120;       // keep it lightweight
  var MOUSE_DIST = 120;        // repel radius (px)
  var MOUSE_FORCE = 6;
  var SPAWN_BATCH = 3;         // bananas added per frame initially
  var BASE_OPACITY = 0.12;     // subtle background feel

  // ── State ───────────────────────────────────────────
  var bananas = [];
  var mouseX = -9999, mouseY = -9999;
  var clicked = false;
  var img = new Image();
  img.crossOrigin = "anonymous";
  img.src = "https://s3-us-west-2.amazonaws.com/s.cdpn.io/1524180/Banana.png";
  var ready = false;
  img.onload = function () { ready = true; };

  // ── Resize ──────────────────────────────────────────
  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", resize);
  resize();

  // ── Mouse tracking ──────────────────────────────────
  document.addEventListener("mousemove", function (e) {
    mouseX = e.clientX; mouseY = e.clientY;
  });
  document.addEventListener("mousedown", function () { clicked = true; });
  document.addEventListener("touchstart", function (e) {
    if (e.touches.length) { mouseX = e.touches[0].clientX; mouseY = e.touches[0].clientY; }
    clicked = true;
  }, { passive: true });
  document.addEventListener("touchmove", function (e) {
    if (e.touches.length) { mouseX = e.touches[0].clientX; mouseY = e.touches[0].clientY; }
  }, { passive: true });

  // ── Banana factory ──────────────────────────────────
  function makeBanana(b) {
    var w = canvas.width || window.innerWidth;
    var h = canvas.height || window.innerHeight;
    if (!b) b = {};
    b.x = Math.random() * w;
    b.y = -30 - Math.random() * h * 0.3;
    b.speed = Math.random() * 3 + 0.8;
    b.scale = b.speed / 4;
    b.rotation = Math.random() * 360;
    b.rotSpeed = (Math.random() - 0.5) * 3;
    b.addX = 0;
    b.addY = 0;
    return b;
  }

  // ── Frame loop ──────────────────────────────────────
  function tick() {
    if (!ready) { requestAnimationFrame(tick); return; }

    var w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.globalAlpha = BASE_OPACITY;

    // Spawn
    if (bananas.length < MAX_BANANAS) {
      for (var s = 0; s < SPAWN_BATCH && bananas.length < MAX_BANANAS; s++) {
        bananas.push(makeBanana());
      }
    }

    var factor = clicked ? 4 : 1;
    var dist = clicked ? w / 4 : MOUSE_DIST;
    var force = MOUSE_FORCE * factor;

    for (var i = bananas.length - 1; i >= 0; i--) {
      var b = bananas[i];

      // Physics
      b.y += b.speed;
      b.rotation += b.rotSpeed;
      b.speed *= 1.005;
      b.x += b.addX;
      b.y += b.addY;
      b.addX *= 0.92;
      if (b.addY < 0) b.addY *= 0.92;

      // Mouse repel
      var dx = mouseX - b.x, dy = mouseY - b.y;
      var d = Math.sqrt(dx * dx + dy * dy);
      if (d < dist && d > 0) {
        b.addX = -dx / dist * force * b.scale;
        b.addY = -dy / dist * force * b.scale;
        if (clicked) b.rotSpeed = -dx / dist * 8;
      }

      // Recycle
      if (b.y > h + 40) { makeBanana(b); }

      // Draw
      ctx.save();
      ctx.translate(b.x, b.y);
      ctx.rotate(b.rotation * Math.PI / 180);
      var sz = img.naturalWidth * b.scale;
      ctx.drawImage(img, -sz / 2, -sz / 2, sz, sz);
      ctx.restore();
    }

    clicked = false;
    ctx.globalAlpha = 1;
    requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
})();
