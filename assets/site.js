(function () {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  var bar = document.querySelector('.progress-bar');
  if (bar) {
    var update = function () {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
    };
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  /* Sticky TOC: the last heading above the chrome wins; nothing at page top.
     On narrow screens the active item is scrolled into view. */
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc a[href^="#"]'));
  var pairs = [];
  links.forEach(function (a) {
    var el = document.getElementById(a.getAttribute('href').slice(1));
    if (el) pairs.push([el, a]);
  });
  if (pairs.length) {
    var tocBox = document.querySelector('.toc .wrap');
    var topbar = document.querySelector('.topbar');
    var toc = document.querySelector('.toc');
    var ticking = false;
    var spy = function () {
      ticking = false;
      var chrome = (topbar ? topbar.offsetHeight : 0) + (toc ? toc.offsetHeight : 0) + 24;
      var cur = null;
      pairs.forEach(function (pair) {
        if (pair[0].getBoundingClientRect().top <= chrome) cur = pair[1];
      });
      links.forEach(function (l) { l.classList.toggle('active', l === cur); });
      if (cur && tocBox) {
        var r = cur.getBoundingClientRect();
        var b = tocBox.getBoundingClientRect();
        if (r.left < b.left + 4 || r.right > b.right - 4) {
          var target = tocBox.scrollLeft + (r.left - b.left)
            - (tocBox.clientWidth - r.width) / 2;
          tocBox.scrollTo({ left: target, behavior: 'smooth' });
        }
      }
    };
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(spy); }
    }, { passive: true });
    window.addEventListener('resize', spy);
    spy();
  }

  /* Smooth in-page anchors; the skip link moves real focus. */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var id = a.getAttribute('href');
      if (id.length < 2) return;
      var el = document.querySelector(id);
      if (!el) return;
      if (a.classList.contains('skip-link')) {
        e.preventDefault();
        el.setAttribute('tabindex', '-1');
        el.focus({ preventScroll: true });
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
      e.preventDefault();
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      try { history.replaceState(null, '', id); } catch (err) {}
    });
  });

  /* Mark tables that need horizontal scrolling, and expose them to keyboard. */
  var markTables = function () {
    document.querySelectorAll('.table-wrap').forEach(function (w) {
      var scrollable = w.scrollWidth > w.clientWidth + 2;
      w.classList.toggle('is-scrollable', scrollable);
      if (scrollable) {
        w.setAttribute('tabindex', '0');
        w.setAttribute('role', 'region');
        w.setAttribute('aria-label', '数据表，可横向滚动');
      } else {
        w.removeAttribute('tabindex');
        w.removeAttribute('role');
        w.removeAttribute('aria-label');
      }
    });
  };
  window.addEventListener('load', function () {
    markTables();
    setTimeout(markTables, 300);
  });
  window.addEventListener('resize', markTables);

  var figures = Array.prototype.slice.call(document.querySelectorAll('figure img'));
  if (figures.length) {
    var box = document.createElement('div');
    box.className = 'lightbox';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', '图片预览');
    var blank = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==';
    box.innerHTML = '<button class="lb-close" type="button">关闭 ✕</button><img alt="" src="' + blank + '"><div class="lb-hint">点击背景或按 Esc 关闭 · 大图可滚动查看</div>';
    document.body.appendChild(box);
    var big = box.querySelector('img');
    var closeBtn = box.querySelector('.lb-close');
    var lastFocus = null;
    var close = function () {
      box.classList.remove('open', 'lb-large');
      document.body.style.overflow = '';
      big.src = blank;
      if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
    };
    var open = function (img) {
      var src = img.dataset.full || img.currentSrc || img.src;
      if (!src) return;
      lastFocus = img;
      big.src = src;
      big.alt = img.alt || '';
      box.classList.toggle('lb-large', img.naturalWidth > 1600 || img.naturalHeight > 1600);
      box.classList.add('open');
      document.body.style.overflow = 'hidden';
      closeBtn.focus({ preventScroll: true });
    };
    figures.forEach(function (img) {
      img.title = '点击放大';
      img.setAttribute('tabindex', '0');
      img.setAttribute('role', 'button');
      img.setAttribute('aria-label', '放大图片' + (img.alt ? '：' + img.alt : ''));
      img.addEventListener('click', function () { open(img); });
      img.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(img); }
      });
    });
    box.addEventListener('click', function (e) {
      if (e.target === box || e.target.classList.contains('lb-close')) close();
    });
    box.addEventListener('keydown', function (e) {
      if (e.key === 'Tab') { e.preventDefault(); closeBtn.focus(); }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && box.classList.contains('open')) close();
    });
  }
  /* Print: lazy images below the fold must be fetched before the dialog opens. */
  window.addEventListener('beforeprint', function () {
    document.querySelectorAll('img[loading="lazy"]').forEach(function (img) {
      img.loading = 'eager';
      if (!img.complete) img.src = img.src;
    });
  });
})();
