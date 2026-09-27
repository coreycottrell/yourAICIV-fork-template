/*
 * client-starter behaviour, loaded by both base templates.
 * The Content-Security-Policy forbids inline <script> and inline on*=
 * handlers, so every behaviour lives here and is attached via data-*:
 *   data-confirm="text"        confirm() before a form submits / button acts
 *   data-autosubmit            submit the parent form when a field changes
 *   data-copy-target="id"      copy that input's value to the clipboard
 *   data-hide-on-error         hide a broken <img>; data-show-next shows its sibling
 *   data-progress-url="url"    campaign send progress poller
 */
(function () {
    'use strict';

    // CSRF: add the token to any form that lacks it (server-side templates
    // also render it explicitly where it matters).
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) {
        var token = meta.getAttribute('content');
        document.querySelectorAll('form').forEach(function (form) {
            if (!form.querySelector('input[name="csrf_token"]')) {
                var input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'csrf_token';
                input.value = token;
                form.appendChild(input);
            }
        });
    }

    document.addEventListener('submit', function (e) {
        var form = e.target;
        var msg = form.getAttribute('data-confirm');
        if (msg && !window.confirm(msg)) { e.preventDefault(); }
    }, true);

    document.addEventListener('click', function (e) {
        var el = e.target.closest('[data-confirm]');
        if (el && el.tagName !== 'FORM' && !window.confirm(el.getAttribute('data-confirm'))) {
            e.preventDefault();
            return;
        }
        var copyBtn = e.target.closest('[data-copy-target]');
        if (copyBtn) {
            var src = document.getElementById(copyBtn.getAttribute('data-copy-target'));
            if (src && navigator.clipboard) {
                navigator.clipboard.writeText(src.value);
                var old = copyBtn.textContent;
                copyBtn.textContent = 'Copied!';
                setTimeout(function () { copyBtn.textContent = old; }, 2000);
            }
        }
    });

    document.addEventListener('change', function (e) {
        if (e.target.hasAttribute && e.target.hasAttribute('data-autosubmit') && e.target.form) {
            e.target.form.submit();
        }
    });

    document.querySelectorAll('img[data-hide-on-error]').forEach(function (img) {
        function hide() {
            img.style.display = 'none';
            if (img.hasAttribute('data-show-next') && img.nextElementSibling) {
                img.nextElementSibling.style.display = 'inline';
            }
        }
        if (img.complete && img.naturalWidth === 0) { hide(); }
        img.addEventListener('error', hide);
    });

    var progress = document.querySelector('[data-progress-url]');
    if (progress) {
        var url = progress.getAttribute('data-progress-url');
        (function poll() {
            fetch(url, { credentials: 'same-origin' })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    var out = document.getElementById('progress-count');
                    if (out) { out.textContent = d.sent_count; }
                    if (d.status === 'sending') { setTimeout(poll, 3000); }
                    else { location.reload(); }
                });
        })();
    }
})();
