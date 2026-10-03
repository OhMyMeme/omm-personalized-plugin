/* 个性化插件：读取插件设置，把背景/字体应用到主窗口（宿主按 defer 文档序注入，
   位于宿主脚本之后执行）。设置保存后宿主推送 omm-plugin-refresh 事件重新应用。 */
(function () {
  var PID = "personalized";
  var STYLE_ID = "omm-personalized-style";

  function safeColor(s) {
    return String(s || "").replace(/[^#a-zA-Z0-9(),.\s]/g, "").trim();
  }

  function safeFont(s) {
    return String(s || "")
      .replace(/[^a-zA-Z0-9一-龥 ,.'()-]/g, "")
      .trim();
  }

  function apply(prefs) {
    var css = "";
    var bg = safeColor(prefs.bg_color);
    if (bg) {
      css += ":root{--bg:" + bg + " !important}";
      css += "html,body{background:" + bg + " !important}";
    }
    var ff = safeFont(prefs.font_family);
    var fs = Number(prefs.font_size) || 0;
    if (ff || fs > 0) {
      css += "body,input,button,textarea,select{";
      if (ff) css += "font-family:" + ff + ",sans-serif;";
      if (fs > 0) css += "font-size:" + Math.min(Math.max(fs, 8), 40) + "px;";
      css += "}";
    }
    var el = document.getElementById(STYLE_ID);
    if (!css) {
      if (el) el.remove();
      return;
    }
    if (!el) {
      el = document.createElement("style");
      el.id = STYLE_ID;
      document.head.appendChild(el);
    }
    el.textContent = css;
  }

  function fetchPrefs() {
    var api = window.pywebview && window.pywebview.api;
    if (api && api.plugin_call) {
      return api.plugin_call(PID, "get_prefs", []);
    }
    return new Promise(function (resolve) {
      window.addEventListener("pywebviewready", function once() {
        window.removeEventListener("pywebviewready", once);
        resolve(window.pywebview.api.plugin_call(PID, "get_prefs", []));
      });
    });
  }

  function refresh() {
    fetchPrefs().then(
      function (r) {
        if (r && typeof r === "object" && !r.error) apply(r);
      },
      function () {}
    );
  }

  refresh();
  window.addEventListener("omm-plugin-refresh", function (e) {
    if (!e.detail || !e.detail.plugin_id || e.detail.plugin_id === PID) refresh();
  });
})();
