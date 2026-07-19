/* ============================================================
   小神农中医AI - 动效引擎（xsn-motion.js）
   vanilla JS，零依赖。动效规约见 frontend/DESIGN.md。
   功能：入场 reveal / 数字计数 / SVG 描边 / 视差 / 规范弹窗
   ============================================================ */
(function () {
    'use strict';

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------- 入场 reveal：data-reveal，可配 data-reveal-delay ---------- */
    function initReveal(root) {
        var els = (root || document).querySelectorAll('[data-reveal]:not(.xsn-revealed)');
        if (!els.length) return;
        if (reducedMotion || !('IntersectionObserver' in window)) {
            els.forEach(function (el) { el.classList.add('xsn-revealed'); });
            return;
        }
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                var el = entry.target;
                var delay = parseInt(el.getAttribute('data-reveal-delay') || '0', 10);
                el.style.setProperty('--reveal-delay', delay + 'ms');
                el.classList.add('xsn-revealed');
                io.unobserve(el);
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
        els.forEach(function (el) { io.observe(el); });
    }

    /* ---------- 数字计数：data-counter="125005" data-counter-duration="1500" ---------- */
    function animateCounter(el) {
        var target = parseFloat(el.getAttribute('data-counter'));
        if (isNaN(target)) return;
        var duration = parseInt(el.getAttribute('data-counter-duration') || '1500', 10);
        if (reducedMotion) { el.textContent = target.toLocaleString('zh-CN'); return; }
        var start = null;
        function step(ts) {
            if (!start) start = ts;
            var p = Math.min(1, (ts - start) / duration);
            /* easeOutExpo：与 --ease-spring 同族，临界阻尼感 */
            var eased = p === 1 ? 1 : 1 - Math.pow(2, -10 * p);
            el.textContent = Math.round(target * eased).toLocaleString('zh-CN');
            if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    function initCounters(root) {
        var els = (root || document).querySelectorAll('[data-counter]');
        if (!els.length) return;
        if (!('IntersectionObserver' in window)) {
            els.forEach(animateCounter);
            return;
        }
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                animateCounter(entry.target);
                io.unobserve(entry.target);
            });
        }, { threshold: 0.4 });
        els.forEach(function (el) { io.observe(el); });
    }

    /* ---------- SVG 描边：data-draw 的 path，进视野画线 ---------- */
    function initDraw(root) {
        var els = (root || document).querySelectorAll('[data-draw]');
        if (!els.length) return;
        els.forEach(function (el) {
            var len = 0;
            try { len = el.getTotalLength(); } catch (e) { return; }
            el.style.strokeDasharray = len;
            el.style.strokeDashoffset = reducedMotion ? 0 : len;
            el.setAttribute('data-draw-len', len);
        });
        if (reducedMotion || !('IntersectionObserver' in window)) return;
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                var el = entry.target;
                el.style.strokeDashoffset = '0';
                io.unobserve(el);
            });
        }, { threshold: 0.3 });
        els.forEach(function (el) { io.observe(el); });
    }

    /* ---------- 视差：容器 data-parallax，层 data-parallax-depth="0.3" ----------
       鼠标 + 滚动双源驱动，rAF 节流；reduced-motion 时完全跳过。 */
    function initParallax(container) {
        if (reducedMotion || !container) return;
        var layers = container.querySelectorAll('[data-parallax-depth]');
        if (!layers.length) return;
        var mx = 0, my = 0, scrollY = 0, ticking = false;

        function apply() {
            ticking = false;
            layers.forEach(function (layer) {
                var depth = parseFloat(layer.getAttribute('data-parallax-depth')) || 0;
                var tx = mx * depth * 30;
                var ty = (my * depth * 20) + (scrollY * depth * 0.25);
                layer.style.transform = 'translate3d(' + tx.toFixed(1) + 'px,' + ty.toFixed(1) + 'px,0)';
            });
        }
        function request() { if (!ticking) { ticking = true; requestAnimationFrame(apply); } }

        container.addEventListener('pointermove', function (e) {
            var r = container.getBoundingClientRect();
            mx = (e.clientX - r.left) / r.width - 0.5;
            my = (e.clientY - r.top) / r.height - 0.5;
            request();
        }, { passive: true });
        window.addEventListener('scroll', function () {
            var r = container.getBoundingClientRect();
            if (r.bottom < 0 || r.top > window.innerHeight) return;
            scrollY = -r.top;
            request();
        }, { passive: true });
    }

    /* ---------- 规范弹窗 ----------
       XSNModal.open(overlay, triggerEl)：从触发元素位置长出（空间一致性），
       materialize（blur+scale+opacity 同动），进出同路；
       XSNModal.close(overlay)：原路收回，焦点归还触发元素。
       依赖 CSS：.xsn-m-overlay（遮罩）/.xsn-m-dialog（卡片），主题包外页面可自带。 */
    var modalState = { overlay: null, trigger: null };

    function modalOpen(overlay, triggerEl) {
        if (!overlay) return;
        var dialog = overlay.querySelector('.xsn-m-dialog') || overlay.firstElementChild;
        modalState.overlay = overlay;
        modalState.trigger = triggerEl || document.activeElement;

        var originX = 50, originY = 50;
        if (triggerEl && dialog && dialog.getBoundingClientRect) {
            overlay.classList.add('active');
            overlay.style.display = 'flex';
            var dr = dialog.getBoundingClientRect();
            var tr = triggerEl.getBoundingClientRect();
            originX = ((tr.left + tr.width / 2 - dr.left) / Math.max(1, dr.width)) * 100;
            originY = ((tr.top + tr.height / 2 - dr.top) / Math.max(1, dr.height)) * 100;
            dialog.style.transformOrigin = originX + '% ' + originY + '%';
        }
        overlay.classList.add('active');
        overlay.style.display = 'flex';
        if (!reducedMotion) {
            overlay.classList.add('xsn-m-enter');
            requestAnimationFrame(function () {
                requestAnimationFrame(function () { overlay.classList.add('xsn-m-in'); });
            });
        }
        var focusable = overlay.querySelector('input, button, [tabindex]');
        if (focusable) setTimeout(function () { focusable.focus(); }, 80);
        document.addEventListener('keydown', modalEscHandler);
    }

    function modalClose(overlay) {
        overlay = overlay || modalState.overlay;
        if (!overlay) return;
        if (!reducedMotion) {
            overlay.classList.remove('xsn-m-in');
            /* 进出同路：等收回动画结束再隐藏 */
            setTimeout(function () {
                overlay.classList.remove('active', 'xsn-m-enter');
                overlay.style.display = '';
            }, 220);
        } else {
            overlay.classList.remove('active', 'xsn-m-enter', 'xsn-m-in');
            overlay.style.display = '';
        }
        if (modalState.trigger && modalState.trigger.focus) modalState.trigger.focus();
        modalState.overlay = null;
        document.removeEventListener('keydown', modalEscHandler);
    }

    function modalEscHandler(e) {
        if (e.key === 'Escape' && modalState.overlay) modalClose(modalState.overlay);
    }

    /* ---------- 自动初始化 ---------- */
    function initAll(root) {
        initReveal(root);
        initCounters(root);
        initDraw(root);
        document.querySelectorAll('[data-parallax]').forEach(initParallax);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { initAll(document); });
    } else {
        initAll(document);
    }

    window.XSNMotion = {
        init: initAll,
        initReveal: initReveal,
        reducedMotion: reducedMotion
    };
    window.XSNModal = { open: modalOpen, close: modalClose };
})();
