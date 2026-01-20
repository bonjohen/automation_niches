/**
 * SMB Compliance Automation Platform
 * Marketing Site JavaScript
 */

// Copy source link to clipboard (global function for onclick handlers)
function copySourceLink(url, button) {
  navigator.clipboard.writeText(url).then(function() {
    // Show copied feedback
    const originalText = button.innerHTML;
    button.classList.add('copied');
    button.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg> Copied!';

    // Reset after 2 seconds
    setTimeout(function() {
      button.classList.remove('copied');
      button.innerHTML = originalText;
    }, 2000);
  }).catch(function(err) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = url;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      button.classList.add('copied');
      const originalText = button.innerHTML;
      button.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg> Copied!';
      setTimeout(function() {
        button.classList.remove('copied');
        button.innerHTML = originalText;
      }, 2000);
    } catch (e) {
      console.error('Copy failed:', e);
    }
    document.body.removeChild(textArea);
  });
}

(function() {
  'use strict';

  // Mobile Navigation Toggle
  function initMobileNav() {
    const toggle = document.querySelector('.nav__toggle');
    const links = document.querySelector('.nav__links');

    if (!toggle || !links) return;

    toggle.addEventListener('click', function() {
      links.classList.toggle('nav__links--open');

      // Update aria-expanded
      const isOpen = links.classList.contains('nav__links--open');
      toggle.setAttribute('aria-expanded', isOpen);
    });

    // Close menu when clicking a link
    links.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        links.classList.remove('nav__links--open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
      if (!toggle.contains(e.target) && !links.contains(e.target)) {
        links.classList.remove('nav__links--open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Smooth scroll for anchor links
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
      anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href === '#') return;

        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          const headerHeight = document.querySelector('.header')?.offsetHeight || 0;
          const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight - 20;

          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });
        }
      });
    });
  }

  // Header scroll effect
  function initHeaderScroll() {
    const header = document.querySelector('.header');
    if (!header) return;

    let lastScroll = 0;

    window.addEventListener('scroll', function() {
      const currentScroll = window.pageYOffset;

      // Add shadow when scrolled
      if (currentScroll > 10) {
        header.style.boxShadow = '0 1px 3px 0 rgb(0 0 0 / 0.1)';
      } else {
        header.style.boxShadow = 'none';
      }

      lastScroll = currentScroll;
    });
  }

  // Form validation
  function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');

    forms.forEach(function(form) {
      form.addEventListener('submit', function(e) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');

        requiredFields.forEach(function(field) {
          // Remove existing error state
          field.classList.remove('form__input--error');

          if (!field.value.trim()) {
            isValid = false;
            field.classList.add('form__input--error');
          }

          // Email validation
          if (field.type === 'email' && field.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(field.value)) {
              isValid = false;
              field.classList.add('form__input--error');
            }
          }
        });

        if (!isValid) {
          e.preventDefault();
          // Focus first error field
          const firstError = form.querySelector('.form__input--error');
          if (firstError) {
            firstError.focus();
          }
        }
      });
    });
  }

  // Animate elements on scroll
  function initScrollAnimation() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    document.querySelectorAll('.card, .feature, .step').forEach(function(el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      observer.observe(el);
    });

    // Add animation class styles
    const style = document.createElement('style');
    style.textContent = '.animate-in { opacity: 1 !important; transform: translateY(0) !important; }';
    document.head.appendChild(style);
  }

  // Solution filter (for solutions index page)
  function initSolutionFilter() {
    const filterButtons = document.querySelectorAll('[data-filter]');
    const solutions = document.querySelectorAll('[data-category]');

    if (!filterButtons.length || !solutions.length) return;

    filterButtons.forEach(function(button) {
      button.addEventListener('click', function() {
        const filter = this.dataset.filter;

        // Update active button
        filterButtons.forEach(function(btn) {
          btn.classList.remove('btn--primary');
          btn.classList.add('btn--secondary');
        });
        this.classList.remove('btn--secondary');
        this.classList.add('btn--primary');

        // Filter solutions
        solutions.forEach(function(solution) {
          if (filter === 'all' || solution.dataset.category === filter) {
            solution.style.display = '';
          } else {
            solution.style.display = 'none';
          }
        });
      });
    });
  }

  // Active navigation link
  function initActiveNav() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav__link');

    navLinks.forEach(function(link) {
      const href = link.getAttribute('href');
      if (href && currentPath.endsWith(href)) {
        link.classList.add('nav__link--active');
      }
    });
  }

  // Statistics Ticker - duplicate content for seamless loop + touch support
  function initStatsTicker() {
    const ticker = document.getElementById('statsTicker');
    if (!ticker) return;

    // Clone all items for seamless infinite scroll
    const items = ticker.querySelectorAll('.ticker-item');
    items.forEach(function(item) {
      const clone = item.cloneNode(true);
      ticker.appendChild(clone);
    });

    // Desktop: Add delayed animation pause/resume on hover
    let resumeTimeout = null;
    let hoveredItem = null;
    let isOverTooltip = false;

    // Get all ticker items (including clones)
    const allItems = ticker.querySelectorAll('.ticker-item');

    allItems.forEach(function(item) {
      const tooltip = item.querySelector('.ticker-tooltip');

      item.addEventListener('mouseenter', function() {
        // Clear any pending resume
        if (resumeTimeout) {
          clearTimeout(resumeTimeout);
          resumeTimeout = null;
        }
        // Pause immediately
        ticker.classList.add('ticker-track--paused');
        // Track hovered item for delayed hide
        if (hoveredItem && hoveredItem !== item) {
          hoveredItem.classList.remove('ticker-item--hovered');
        }
        hoveredItem = item;
        item.classList.add('ticker-item--hovered');
      });

      item.addEventListener('mouseleave', function(e) {
        const currentItem = item;

        // Delay resuming - check mouse position at end of delay
        resumeTimeout = setTimeout(function() {
          // Check if mouse is now over tooltip or the item
          if (!isOverTooltip && hoveredItem === currentItem) {
            currentItem.classList.remove('ticker-item--hovered');
            ticker.classList.remove('ticker-track--paused');
            hoveredItem = null;
          }
        }, 500);
      });

      // Track mouse entering/leaving tooltip
      if (tooltip) {
        tooltip.addEventListener('mouseenter', function() {
          isOverTooltip = true;
          // Clear any pending resume since we're on tooltip
          if (resumeTimeout) {
            clearTimeout(resumeTimeout);
            resumeTimeout = null;
          }
          // Ensure item stays hovered
          item.classList.add('ticker-item--hovered');
          ticker.classList.add('ticker-track--paused');
        });

        tooltip.addEventListener('mouseleave', function() {
          isOverTooltip = false;
          // Start the delay to resume
          resumeTimeout = setTimeout(function() {
            if (!isOverTooltip) {
              item.classList.remove('ticker-item--hovered');
              ticker.classList.remove('ticker-track--paused');
              hoveredItem = null;
            }
          }, 500);
        });
      }
    });

    // Touch support for mobile devices
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

    if (isTouchDevice) {
      let activeItem = null;

      // Add close buttons to all tooltips
      ticker.querySelectorAll('.ticker-tooltip').forEach(function(tooltip) {
        const closeBtn = document.createElement('button');
        closeBtn.className = 'ticker-tooltip__close';
        closeBtn.innerHTML = '&times;';
        closeBtn.setAttribute('aria-label', 'Close');
        tooltip.insertBefore(closeBtn, tooltip.firstChild);
      });

      // Handle tap on ticker items
      ticker.addEventListener('click', function(e) {
        const item = e.target.closest('.ticker-item');
        const closeBtn = e.target.closest('.ticker-tooltip__close');
        const copyBtn = e.target.closest('.copy-link-btn');

        // If close button clicked, close tooltip
        if (closeBtn) {
          e.preventDefault();
          e.stopPropagation();
          closeActiveTooltip();
          return;
        }

        // If copy button clicked, let it work normally
        if (copyBtn) {
          return;
        }

        // If clicking on a ticker item
        if (item) {
          e.preventDefault();

          // If same item, toggle off
          if (activeItem === item) {
            closeActiveTooltip();
          } else {
            // Close previous, open new
            closeActiveTooltip();
            openTooltip(item);
          }
        }
      });

      // Close when tapping outside
      document.addEventListener('click', function(e) {
        if (activeItem && !e.target.closest('.ticker-item')) {
          closeActiveTooltip();
        }
      });

      function openTooltip(item) {
        activeItem = item;
        item.classList.add('ticker-item--active');
        ticker.style.animationPlayState = 'paused';
      }

      function closeActiveTooltip() {
        if (activeItem) {
          activeItem.classList.remove('ticker-item--active');
          activeItem = null;
          ticker.style.animationPlayState = 'running';
        }
      }
    }
  }

  // Initialize all functions on DOM ready
  function init() {
    initMobileNav();
    initSmoothScroll();
    initHeaderScroll();
    initFormValidation();
    initScrollAnimation();
    initSolutionFilter();
    initActiveNav();
    initStatsTicker();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
