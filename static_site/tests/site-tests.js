/**
 * SMB Compliance Automation - Static Site Test Suite
 *
 * Automated tests for navigation, accessibility, SEO, and functionality.
 * Run these tests via browser console or automation tools.
 *
 * Usage:
 * 1. Open any page of the site in a browser
 * 2. Open DevTools Console (F12)
 * 3. Copy and paste this entire file
 * 4. Run: runAllTests()
 */

const SiteTests = {
  results: [],
  currentPage: window.location.pathname,

  // Test result recording
  pass(category, test, details = '') {
    this.results.push({ status: 'PASS', category, test, details });
    console.log(`✅ [${category}] ${test}${details ? ': ' + details : ''}`);
  },

  fail(category, test, details = '') {
    this.results.push({ status: 'FAIL', category, test, details });
    console.error(`❌ [${category}] ${test}${details ? ': ' + details : ''}`);
  },

  warn(category, test, details = '') {
    this.results.push({ status: 'WARN', category, test, details });
    console.warn(`⚠️ [${category}] ${test}${details ? ': ' + details : ''}`);
  },

  // ==========================================
  // Navigation Tests
  // ==========================================
  testNavigation() {
    console.group('🔗 Navigation Tests');

    // Test skip link
    const skipLink = document.querySelector('.skip-link');
    if (skipLink && skipLink.getAttribute('href') === '#main-content') {
      const mainContent = document.getElementById('main-content');
      if (mainContent) {
        this.pass('Navigation', 'Skip link present and valid');
      } else {
        this.fail('Navigation', 'Skip link target #main-content not found');
      }
    } else {
      this.fail('Navigation', 'Skip link missing or invalid');
    }

    // Test header navigation links
    const navLinks = document.querySelectorAll('.nav__link, .nav__links a');
    const brokenLinks = [];
    navLinks.forEach(link => {
      const href = link.getAttribute('href');
      if (!href || href === '#' || href.startsWith('javascript:')) {
        brokenLinks.push(link.textContent.trim());
      }
    });
    if (brokenLinks.length === 0) {
      this.pass('Navigation', `All ${navLinks.length} nav links have valid hrefs`);
    } else {
      this.fail('Navigation', 'Broken nav links found', brokenLinks.join(', '));
    }

    // Test anchor links point to existing IDs
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    const missingAnchors = [];
    anchorLinks.forEach(link => {
      const href = link.getAttribute('href');
      if (href !== '#' && href.length > 1) {
        const targetId = href.substring(1);
        if (!document.getElementById(targetId)) {
          missingAnchors.push(href);
        }
      }
    });
    if (missingAnchors.length === 0) {
      this.pass('Navigation', 'All anchor links point to existing IDs');
    } else {
      this.fail('Navigation', 'Missing anchor targets', missingAnchors.join(', '));
    }

    // Test for empty href links
    const emptyHrefs = document.querySelectorAll('a[href=""], a:not([href])');
    if (emptyHrefs.length === 0) {
      this.pass('Navigation', 'No empty href links');
    } else {
      this.fail('Navigation', `Found ${emptyHrefs.length} empty href links`);
    }

    console.groupEnd();
  },

  // ==========================================
  // Accessibility Tests
  // ==========================================
  testAccessibility() {
    console.group('♿ Accessibility Tests');

    // DOCTYPE
    if (document.doctype) {
      this.pass('Accessibility', 'DOCTYPE present');
    } else {
      this.fail('Accessibility', 'DOCTYPE missing');
    }

    // HTML lang attribute
    const htmlLang = document.documentElement.lang;
    if (htmlLang) {
      this.pass('Accessibility', `HTML lang attribute set: ${htmlLang}`);
    } else {
      this.fail('Accessibility', 'HTML lang attribute missing');
    }

    // Meta viewport
    const viewport = document.querySelector('meta[name="viewport"]');
    if (viewport) {
      this.pass('Accessibility', 'Meta viewport present');
    } else {
      this.fail('Accessibility', 'Meta viewport missing');
    }

    // Single H1
    const h1s = document.querySelectorAll('h1');
    if (h1s.length === 1) {
      this.pass('Accessibility', 'Single H1 on page');
    } else if (h1s.length === 0) {
      this.fail('Accessibility', 'No H1 found on page');
    } else {
      this.warn('Accessibility', `Multiple H1s found: ${h1s.length}`);
    }

    // Heading hierarchy
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let prevLevel = 0;
    let skippedLevels = false;
    headings.forEach(h => {
      const level = parseInt(h.tagName.charAt(1));
      if (prevLevel > 0 && level > prevLevel + 1) {
        skippedLevels = true;
      }
      prevLevel = level;
    });
    if (!skippedLevels) {
      this.pass('Accessibility', 'Heading hierarchy is valid');
    } else {
      this.warn('Accessibility', 'Skipped heading levels detected');
    }

    // Images with alt text
    const images = document.querySelectorAll('img');
    const missingAlt = Array.from(images).filter(img => !img.hasAttribute('alt'));
    if (missingAlt.length === 0) {
      this.pass('Accessibility', `All ${images.length} images have alt attributes`);
    } else {
      this.fail('Accessibility', `${missingAlt.length} images missing alt attribute`);
    }

    // Interactive elements with accessible names
    const buttons = document.querySelectorAll('button');
    const unlabeledButtons = Array.from(buttons).filter(btn => {
      const text = btn.textContent.trim();
      const ariaLabel = btn.getAttribute('aria-label');
      const ariaLabelledby = btn.getAttribute('aria-labelledby');
      return !text && !ariaLabel && !ariaLabelledby;
    });
    if (unlabeledButtons.length === 0) {
      this.pass('Accessibility', `All ${buttons.length} buttons have accessible names`);
    } else {
      this.fail('Accessibility', `${unlabeledButtons.length} buttons missing accessible names`);
    }

    // No positive tabindex
    const positiveTabindex = document.querySelectorAll('[tabindex]:not([tabindex="-1"]):not([tabindex="0"])');
    if (positiveTabindex.length === 0) {
      this.pass('Accessibility', 'No positive tabindex values');
    } else {
      this.fail('Accessibility', `Found ${positiveTabindex.length} elements with positive tabindex`);
    }

    // Semantic HTML
    const semantic = {
      header: document.querySelector('header'),
      main: document.querySelector('main'),
      footer: document.querySelector('footer'),
      nav: document.querySelector('nav')
    };
    const missingElements = Object.entries(semantic)
      .filter(([_, el]) => !el)
      .map(([name]) => name);
    if (missingElements.length === 0) {
      this.pass('Accessibility', 'All semantic landmarks present (header, main, footer, nav)');
    } else {
      this.fail('Accessibility', 'Missing semantic elements', missingElements.join(', '));
    }

    console.groupEnd();
  },

  // ==========================================
  // SEO Tests
  // ==========================================
  testSEO() {
    console.group('🔍 SEO Tests');

    // Title tag
    const title = document.querySelector('title');
    if (title && title.textContent.trim()) {
      const titleLen = title.textContent.length;
      if (titleLen <= 60) {
        this.pass('SEO', `Title tag present (${titleLen} chars)`);
      } else {
        this.warn('SEO', `Title tag too long: ${titleLen} chars (recommended: 60)`);
      }
    } else {
      this.fail('SEO', 'Title tag missing or empty');
    }

    // Meta description
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc && metaDesc.content.trim()) {
      const descLen = metaDesc.content.length;
      if (descLen <= 160) {
        this.pass('SEO', `Meta description present (${descLen} chars)`);
      } else {
        this.warn('SEO', `Meta description too long: ${descLen} chars (recommended: 160)`);
      }
    } else {
      this.fail('SEO', 'Meta description missing or empty');
    }

    // Open Graph tags
    const ogTitle = document.querySelector('meta[property="og:title"]');
    const ogDesc = document.querySelector('meta[property="og:description"]');
    const ogImage = document.querySelector('meta[property="og:image"]');
    if (ogTitle && ogDesc && ogImage) {
      this.pass('SEO', 'Open Graph tags present');
    } else {
      this.warn('SEO', 'Open Graph tags incomplete or missing');
    }

    // Canonical URL
    const canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) {
      this.pass('SEO', `Canonical URL defined: ${canonical.href}`);
    } else {
      this.warn('SEO', 'Canonical URL not defined');
    }

    // Descriptive link text
    const genericLinkTexts = ['click here', 'read more', 'learn more', 'more', 'here'];
    const links = document.querySelectorAll('a');
    const genericLinks = Array.from(links).filter(link => {
      const text = link.textContent.trim().toLowerCase();
      return genericLinkTexts.includes(text);
    });
    if (genericLinks.length === 0) {
      this.pass('SEO', 'No generic link text found');
    } else {
      this.warn('SEO', `Found ${genericLinks.length} links with generic text`);
    }

    console.groupEnd();
  },

  // ==========================================
  // Performance Tests
  // ==========================================
  testPerformance() {
    console.group('⚡ Performance Tests');

    // DOM element count
    const elementCount = document.querySelectorAll('*').length;
    if (elementCount < 800) {
      this.pass('Performance', `DOM element count: ${elementCount}`);
    } else if (elementCount < 1500) {
      this.warn('Performance', `DOM element count high: ${elementCount}`);
    } else {
      this.fail('Performance', `DOM element count too high: ${elementCount}`);
    }

    // DOM depth
    function getMaxDepth(element, depth = 0) {
      if (!element.children.length) return depth;
      return Math.max(...Array.from(element.children).map(child => getMaxDepth(child, depth + 1)));
    }
    const maxDepth = getMaxDepth(document.body);
    if (maxDepth <= 15) {
      this.pass('Performance', `DOM depth: ${maxDepth}`);
    } else {
      this.warn('Performance', `DOM depth too deep: ${maxDepth}`);
    }

    // External resources
    const scripts = document.querySelectorAll('script[src]');
    const stylesheets = document.querySelectorAll('link[rel="stylesheet"]');
    this.pass('Performance', `Resources: ${scripts.length} JS, ${stylesheets.length} CSS`);

    // Performance timing (if available)
    if (window.performance && window.performance.timing) {
      const timing = window.performance.timing;
      const domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart;
      const loadTime = timing.loadEventEnd - timing.navigationStart;

      if (domContentLoaded > 0) {
        this.pass('Performance', `DOM Content Loaded: ${domContentLoaded}ms`);
      }
      if (loadTime > 0) {
        this.pass('Performance', `Full Load Time: ${loadTime}ms`);
      }
    }

    console.groupEnd();
  },

  // ==========================================
  // Interactive Element Tests
  // ==========================================
  testInteractiveElements() {
    console.group('🖱️ Interactive Element Tests');

    // Touch target sizes
    const interactiveElements = document.querySelectorAll('button, a, input, select, textarea');
    let smallTargets = [];
    interactiveElements.forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        if (rect.width < 44 || rect.height < 44) {
          smallTargets.push({
            element: el.tagName + (el.className ? '.' + el.className.split(' ')[0] : ''),
            width: Math.round(rect.width),
            height: Math.round(rect.height)
          });
        }
      }
    });
    if (smallTargets.length === 0) {
      this.pass('Interactive', 'All touch targets meet 44x44px minimum');
    } else {
      this.warn('Interactive', `${smallTargets.length} elements below 44x44px`,
        smallTargets.slice(0, 5).map(t => `${t.element} (${t.width}x${t.height})`).join(', '));
    }

    // Buttons have cursor pointer
    const buttonsWithoutPointer = Array.from(document.querySelectorAll('button')).filter(btn => {
      const style = window.getComputedStyle(btn);
      return style.cursor !== 'pointer';
    });
    if (buttonsWithoutPointer.length === 0) {
      this.pass('Interactive', 'All buttons have cursor: pointer');
    } else {
      this.fail('Interactive', `${buttonsWithoutPointer.length} buttons missing cursor: pointer`);
    }

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach((form, index) => {
      const requiredFields = form.querySelectorAll('[required]');
      const labelsForRequired = Array.from(requiredFields).every(field => {
        const label = form.querySelector(`label[for="${field.id}"]`);
        return label || field.getAttribute('aria-label');
      });
      if (labelsForRequired) {
        this.pass('Interactive', `Form ${index + 1}: All required fields have labels`);
      } else {
        this.fail('Interactive', `Form ${index + 1}: Some required fields missing labels`);
      }
    });

    console.groupEnd();
  },

  // ==========================================
  // Console Error Check
  // ==========================================
  testConsoleErrors() {
    console.group('🔴 Console Errors');

    // This captures errors after script loads
    // For comprehensive testing, errors should be captured from page load
    this.pass('Console', 'Test suite loaded without errors');
    this.warn('Console', 'For full error checking, monitor console during page load');

    console.groupEnd();
  },

  // ==========================================
  // Summary
  // ==========================================
  printSummary() {
    console.group('📊 Test Summary');

    const passed = this.results.filter(r => r.status === 'PASS').length;
    const failed = this.results.filter(r => r.status === 'FAIL').length;
    const warnings = this.results.filter(r => r.status === 'WARN').length;
    const total = this.results.length;

    console.log(`Total Tests: ${total}`);
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`⚠️ Warnings: ${warnings}`);
    console.log(`Pass Rate: ${((passed / total) * 100).toFixed(1)}%`);

    if (failed > 0) {
      console.group('Failed Tests:');
      this.results.filter(r => r.status === 'FAIL').forEach(r => {
        console.error(`[${r.category}] ${r.test}${r.details ? ': ' + r.details : ''}`);
      });
      console.groupEnd();
    }

    console.groupEnd();

    return {
      total,
      passed,
      failed,
      warnings,
      passRate: ((passed / total) * 100).toFixed(1) + '%'
    };
  },

  // Run all tests
  runAll() {
    console.clear();
    console.log('%c🧪 SMB Compliance Static Site Test Suite', 'font-size: 18px; font-weight: bold;');
    console.log(`Testing: ${window.location.href}`);
    console.log('-------------------------------------------');

    this.results = [];

    this.testNavigation();
    this.testAccessibility();
    this.testSEO();
    this.testPerformance();
    this.testInteractiveElements();
    this.testConsoleErrors();

    console.log('-------------------------------------------');
    return this.printSummary();
  }
};

// Global function to run all tests
function runAllTests() {
  return SiteTests.runAll();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SiteTests, runAllTests };
}

console.log('Test suite loaded. Run: runAllTests()');
