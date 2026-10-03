/* 个性化插件 · 设置窗口脚本：RGBA+HEX 颜色控件联动、字体下拉补项、启动动画选择与预览。
   宿主在插件区块回填完成后派发 omm-plugin-section-filled 事件，本脚本据当前设置同步控件。 */
(function () {
  var PID = "personalized";

  function api(method) {
    var a = window.pywebview && window.pywebview.api;
    if (!a || typeof a[method] !== "function") return null;
    return a[method];
  }

  /* ── 颜色解析/格式化 ── */

  function parseColor(v) {
    v = String(v || "").trim();
    if (!v) return null;
    if (v.charAt(0) !== "#") v = "#" + v;
    if (/^#[0-9a-fA-F]{3}$/.test(v)) {
      v = "#" + v.charAt(1) + v.charAt(1) + v.charAt(2) + v.charAt(2) + v.charAt(3) + v.charAt(3);
    }
    if (/^#[0-9a-fA-F]{6}$/.test(v)) v += "ff";
    if (!/^#[0-9a-fA-F]{8}$/.test(v)) return null;
    return {
      r: parseInt(v.substr(1, 2), 16),
      g: parseInt(v.substr(3, 2), 16),
      b: parseInt(v.substr(5, 2), 16),
      a: parseInt(v.substr(7, 2), 16),
    };
  }

  function hex2(n) {
    n = Math.max(0, Math.min(255, Math.round(n)));
    return (n < 16 ? "0" : "") + n.toString(16);
  }

  function formatColor(c) {
    var base = "#" + hex2(c.r) + hex2(c.g) + hex2(c.b);
    return c.a < 255 ? base + hex2(c.a) : base;
  }

  function cssColor(c) {
    return c.a >= 255
      ? "rgb(" + c.r + "," + c.g + "," + c.b + ")"
      : "rgba(" + c.r + "," + c.g + "," + c.b + "," + (c.a / 255).toFixed(3) + ")";
  }

  /* ── 颜色控件同步 ── */

  function syncColorBox(box) {
    var hex = box.querySelector(".p-chex");
    if (!hex) return;
    var c = parseColor(hex.value);
    var sw = box.querySelector(".p-cswatch");
    var pick = box.querySelector(".p-cpick");
    var cr = box.querySelector(".p-cr");
    var cg = box.querySelector(".p-cg");
    var cb = box.querySelector(".p-cb");
    var ca = box.querySelector(".p-ca");
    var cav = box.querySelector(".p-caval");
    if (!c) {
      if (sw) {
        sw.style.background =
          "repeating-conic-gradient(#666 0% 25%, #999 0% 50%) 0 0/10px 10px";
      }
      if (cr) cr.value = "";
      if (cg) cg.value = "";
      if (cb) cb.value = "";
      if (ca) ca.value = 255;
      if (cav) cav.textContent = "255";
      return;
    }
    if (pick) pick.value = "#" + hex2(c.r) + hex2(c.g) + hex2(c.b);
    if (cr) cr.value = c.r;
    if (cg) cg.value = c.g;
    if (cb) cb.value = c.b;
    if (ca) ca.value = c.a;
    if (cav) cav.textContent = c.a;
    if (sw) sw.style.background = cssColor(c);
  }

  function writeColor(box, c) {
    var hex = box.querySelector(".p-chex");
    if (!hex) return;
    hex.value = formatColor(c);
    syncColorBox(box);
  }

  function currentColor(box) {
    return parseColor(box.querySelector(".p-chex").value) || {
      r: 0,
      g: 0,
      b: 0,
      a: 255,
    };
  }

  function bindColorBox(box) {
    var pick = box.querySelector(".p-cpick");
    var hex = box.querySelector(".p-chex");
    var cr = box.querySelector(".p-cr");
    var cg = box.querySelector(".p-cg");
    var cb = box.querySelector(".p-cb");
    var ca = box.querySelector(".p-ca");
    if (pick) {
      pick.addEventListener("input", function () {
        var c = currentColor(box);
        var p = parseColor(pick.value);
        if (p) writeColor(box, { r: p.r, g: p.g, b: p.b, a: c.a });
      });
    }
    if (hex) {
      hex.addEventListener("input", function () {
        if (parseColor(hex.value)) syncColorBox(box);
      });
      hex.addEventListener("blur", function () {
        var c = parseColor(hex.value);
        if (c) writeColor(box, c);
        else {
          hex.value = "";
          syncColorBox(box);
        }
      });
    }
    [cr, cg, cb].forEach(function (el, i) {
      if (!el) return;
      el.addEventListener("input", function () {
        var c = currentColor(box);
        c[i === 0 ? "r" : i === 1 ? "g" : "b"] = parseInt(el.value, 10) || 0;
        writeColor(box, c);
      });
    });
    if (ca) {
      ca.addEventListener("input", function () {
        var c = currentColor(box);
        c.a = parseInt(ca.value, 10) || 0;
        writeColor(box, c);
      });
    }
    syncColorBox(box);
  }

  /* ── 字体下拉：保存值不在候选里时补一个选项 ── */

  function ensureFontOption(sel, v) {
    if (!v) return;
    for (var i = 0; i < sel.options.length; i++) {
      if (sel.options[i].value === v) {
        sel.value = v;
        return;
      }
    }
    var o = document.createElement("option");
    o.value = v;
    o.textContent = v + "（自定义）";
    sel.appendChild(o);
    sel.value = v;
  }

  /* ── 启动动画选择与预览 ── */

  function updateIntroPreview() {
    var hid = document.getElementById("p-intro-value");
    var name = document.getElementById("p-intro-name");
    var prev = document.getElementById("p-intro-preview");
    if (!hid || !name || !prev) return;
    var v = hid.value;
    name.textContent = v
      ? "当前：" + v.replace(/^data\//, "")
      : "未设置（默认动画）";
    prev.innerHTML = "";
    if (!v) return;
    var url = "/plugins/" + PID + "/" + v;
    var el;
    if (/\.(mp4|webm|mov|mkv|avi)$/i.test(v)) {
      el = document.createElement("video");
      el.src = url;
      el.controls = true;
      el.muted = true;
      el.loop = false;
    } else {
      el = document.createElement("img");
      el.src = url;
      el.alt = "启动动画预览";
    }
    prev.appendChild(el);
  }

  window.pIntroPick = function (media) {
    var pick = api("plugin_pick_file");
    var call = api("plugin_call");
    if (!pick || !call) {
      showToast("接口未就绪，请重启软件");
      return;
    }
    Promise.resolve(pick(PID, media)).then(function (r) {
      if (!r || !r.ok) {
        if (r && r.cancelled) return;
        showToast("选择文件失败");
        return;
      }
      return Promise.resolve(call(PID, "set_intro", [r.path])).then(function (res) {
        if (res && res.ok) {
          var hid = document.getElementById("p-intro-value");
          if (hid) hid.value = res.path;
          updateIntroPreview();
          showToast("启动动画已更新，重启后生效");
        } else {
          showToast("设置失败：" + ((res && res.error) || "未知错误"));
        }
      });
    }).catch(function () {
      showToast("设置失败");
    });
  };

  window.pIntroClear = function () {
    var call = api("plugin_call");
    if (!call) return;
    Promise.resolve(call(PID, "clear_intro", [])).then(function (res) {
      if (res && res.ok) {
        var hid = document.getElementById("p-intro-value");
        if (hid) hid.value = "";
        updateIntroPreview();
        showToast("已恢复默认启动动画");
      }
    }).catch(function () {});
  };

  /* ── 绑定与宿主回填完成事件 ── */

  function syncAll() {
    document.querySelectorAll(".p-color").forEach(syncColorBox);
    updateIntroPreview();
  }

  document.querySelectorAll(".p-color").forEach(bindColorBox);
  updateIntroPreview();

  window.addEventListener("omm-plugin-section-filled", function (e) {
    if (!e.detail || e.detail.plugin_id !== PID) return;
    var get = api("plugin_get_settings");
    if (!get) return;
    Promise.resolve(get(PID)).then(function (s) {
      if (!s) return;
      var sel = document.querySelector(".p-font-select");
      if (sel) ensureFontOption(sel, String(s.font_family || ""));
      syncAll();
    }).catch(function () {});
  });
})();
