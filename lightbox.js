/* Nav is always visible (position: fixed in CSS). */

/**
 * Mobile hamburger menu toggle.
 */
(function () {
  var toggle = document.querySelector('.nav__toggle');
  var menu = document.getElementById('nav-menu');
  if (!toggle || !menu) return;

  toggle.addEventListener('click', function () {
    var expanded = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!expanded));
    menu.classList.toggle('nav__links--open');
  });

  // Close menu when a navigation link is clicked (not dropdown triggers)
  menu.addEventListener('click', function (e) {
    if (e.target.tagName === 'A' && !e.target.hasAttribute('aria-haspopup')) {
      toggle.setAttribute('aria-expanded', 'false');
      menu.classList.remove('nav__links--open');
    }
  });
})();

/**
 * Dropdown menu: keyboard and touch support.
 */
(function () {
  var triggers = document.querySelectorAll('.nav__dropdown-trigger');

  triggers.forEach(function (trigger) {
    var link = trigger.querySelector('a[aria-haspopup]');
    var dropdown = trigger.querySelector('.nav__dropdown');
    if (!link || !dropdown) return;

    function open() {
      link.setAttribute('aria-expanded', 'true');
      dropdown.classList.add('nav__dropdown--open');
    }

    function close() {
      link.setAttribute('aria-expanded', 'false');
      dropdown.classList.remove('nav__dropdown--open');
    }

    function toggle(e) {
      e.preventDefault();
      if (link.getAttribute('aria-expanded') === 'true') {
        close();
      } else {
        open();
      }
    }

    // Click/touch toggle (works on mobile and desktop)
    link.addEventListener('click', toggle);

    // Keyboard: Enter/Space to toggle, Escape to close
    link.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggle(e);
      }
      if (e.key === 'Escape') {
        close();
        link.focus();
      }
    });

    // Close when clicking outside
    document.addEventListener('click', function (e) {
      if (!trigger.contains(e.target)) {
        close();
      }
    });

    // Escape from within dropdown
    dropdown.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        close();
        link.focus();
      }
    });
  });
})();

/**
 * Lightweight lightbox for diagrams and screenshots.
 * Click any .diagram or .screenshot__frame to expand.
 * Click overlay or press Escape to close.
 * No dependencies.
 */
(function () {
  var overlay = document.createElement('div');
  overlay.className = 'lightbox';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', 'Expanded view — click or press Escape to close');
  overlay.innerHTML = '<div class="lightbox__content"></div>';
  document.body.appendChild(overlay);

  var content = overlay.querySelector('.lightbox__content');
  var isOpen = false;
  var triggerElement = null;

  function open(el) {
    var clone;

    // For diagrams, clone the SVG
    var svg = el.querySelector('svg[role="img"]');
    if (svg) {
      clone = svg.cloneNode(true);
      clone.removeAttribute('width');
      clone.removeAttribute('height');
      clone.style.width = '100%';
      clone.style.height = 'auto';
      clone.style.maxHeight = '90vh';
    }

    // For screenshots with video
    var video = el.querySelector('video');
    if (video) {
      clone = document.createElement('video');
      clone.src = video.querySelector('source').src;
      clone.autoplay = true;
      clone.muted = true;
      clone.loop = true;
      clone.playsInline = true;
      clone.controls = true;
      clone.style.maxWidth = '95vw';
      clone.style.maxHeight = '95vh';
      clone.style.objectFit = 'contain';
    }

    // For screenshots with images
    var img = !clone && el.querySelector('img');
    if (img) {
      clone = document.createElement('img');
      clone.src = img.src;
      clone.alt = img.alt || '';
      clone.style.maxWidth = '95vw';
      clone.style.maxHeight = '95vh';
      clone.style.objectFit = 'contain';
    }

    // For screenshot placeholders (no image yet), skip
    if (!clone) return;

    triggerElement = el;
    content.innerHTML = '';
    content.appendChild(clone);
    overlay.classList.add('lightbox--open');
    isOpen = true;
    document.body.style.overflow = 'hidden';
  }

  function close() {
    overlay.classList.remove('lightbox--open');
    isOpen = false;
    document.body.style.overflow = '';
    // Return focus to trigger element
    if (triggerElement) {
      triggerElement.focus();
      triggerElement = null;
    }
    // Clean up after transition
    setTimeout(function () {
      content.innerHTML = '';
    }, 300);
  }

  // Click to close overlay
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay || e.target === content) {
      close();
    }
  });

  // Also close when clicking the expanded content itself
  content.addEventListener('click', close);

  // Escape to close
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isOpen) close();
  });

  // Make diagrams and screenshots clickable
  document.querySelectorAll('.diagram, .screenshot__frame--has-image, .screenshot:has(.screenshot__image)').forEach(function (el) {
    el.style.cursor = 'zoom-in';
    el.setAttribute('tabindex', '0');
    el.setAttribute('role', 'button');
    el.setAttribute('aria-label', 'Click to expand');

    el.addEventListener('click', function (e) {
      // Don't intercept link clicks inside
      if (e.target.closest('a')) return;
      open(el);
    });

    el.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        open(el);
      }
    });
  });
})();
