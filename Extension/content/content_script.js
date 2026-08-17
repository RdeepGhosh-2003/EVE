/**
 * Extension/content/content_script.js - Version 1.17.41
 * Upgraded executeMasterAction routing logic to strictly evaluate visible password inputs,
 * preventing SPA modal misclassification on Workday and similar web apps.
 */

function isElementVisible(el) {
    if (!el) return false;
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
        return false;
    }
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
}

if (typeof window !== 'undefined' && !window.UniversalMatcher) {
    window.UniversalMatcher = {
        getElementLabelText: function(el) {
            if (el.labels && el.labels.length > 0) {
                return el.labels[0].textContent || '';
            }
            const ariaLabel = el.getAttribute('aria-label') || el.getAttribute('placeholder') || '';
            return ariaLabel;
        }
    };
}

function executeMasterAction(container = document) {
    // Dual-Mode Auth Detection: Strictly target VISIBLE password elements
    const visiblePasswordInputs = Array.from(container.querySelectorAll('input[type="password"]')).filter(el => isElementVisible(el));
    const passwordInputCount = visiblePasswordInputs.length;

    const strictConfirmPassEl = Array.from(container.querySelectorAll('[data-automation-id="confirmPassword"], [data-automation-id="verifyPassword"]')).find(el => isElementVisible(el)) ||
                          visiblePasswordInputs.find(el => {
                            const txt = window.UniversalMatcher.getElementLabelText(el).toLowerCase();
                            return txt.includes('verify') || txt.includes('confirm') || txt.includes('re-enter') || txt.includes('retype');
                          });

    // Account Creation Mode: Strictly rely on presence of verification fields or multiple VISIBLE password inputs
    const isCreateAccountMode = !!(strictConfirmPassEl || passwordInputCount >= 2);

    console.log(`[v1.17.41] Auth Detection: visiblePasswords=${passwordInputCount}, isCreateAccountMode=${isCreateAccountMode}`);

    return {
        isCreateAccountMode,
        passwordInputCount,
        strictConfirmPassEl,
        visiblePasswordInputs
    };
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { executeMasterAction, isElementVisible };
}
