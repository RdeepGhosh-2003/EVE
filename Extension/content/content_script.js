/**
 * Extension/content/content_script.js - Version 1.17.42
 * Fixes asynchronous timing in executeLoginFlow with strict await sequencing,
 * and disables Ghost Data Space+Backspace simulation on Phone fields in simulateHumanTyping.
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
            if (!el) return '';
            if (el.labels && el.labels.length > 0) {
                return el.labels[0].textContent || '';
            }
            return el.getAttribute('aria-label') || el.getAttribute('placeholder') || '';
        }
    };
}

function showToast(message, type = "info") {
    console.log(`[Toast v1.17.42] [${type.toUpperCase()}] ${message}`);
}

function highlightField(element) {
    if (!element) return;
    element.style.outline = '2px solid #3b82f6';
    element.style.transition = 'outline 0.3s ease';
    setTimeout(() => {
        element.style.outline = '';
    }, 1500);
}

function setNativeValue(element, value) {
    const valueSetter = Object.getOwnPropertyDescriptor(element, 'value')?.set;
    const prototype = Object.getPrototypeOf(element);
    const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;

    if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {
        prototypeValueSetter.call(element, value);
    } else if (valueSetter) {
        valueSetter.call(element, value);
    } else {
        element.value = value;
    }
}

async function simulateHumanTyping(element, strVal) {
    if (!element) return;

    function setVal(val) {
        setNativeValue(element, val);
    }

    setVal(strVal);
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));

    const isPhoneField = element.type === 'tel' ||
        (element.name && element.name.toLowerCase().includes('phone')) ||
        (element.id && element.id.toLowerCase().includes('phone'));

    if (!isPhoneField) {
        // 3.5 Ghost Data React State Fix (Space + Backspace Simulation)
        setVal(strVal + " ");
        element.dispatchEvent(new Event('input', { bubbles: true }));
        try {
            element.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, cancelable: true, key: ' ', code: 'Space' }));
            element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, cancelable: true, key: ' ', code: 'Space' }));
        } catch(e) {}

        await new Promise(resolve => setTimeout(resolve, 30));

        setVal(strVal);
        element.dispatchEvent(new Event('input', { bubbles: true }));
        try {
            element.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, cancelable: true, key: 'Backspace', code: 'Backspace' }));
            element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, cancelable: true, key: 'Backspace', code: 'Backspace' }));
        } catch(e) {}
    }
}

function executeConsentAutoCheck(container = document) {
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
        if (!cb.checked && isElementVisible(cb)) {
            cb.checked = true;
            cb.dispatchEvent(new Event('change', { bubbles: true }));
        }
    });
}

function findLoginSubmitButton(container = document) {
    const buttons = Array.from(container.querySelectorAll('button, input[type="submit"]')).filter(el => isElementVisible(el));
    return buttons.find(b => {
        const txt = (b.textContent || b.value || '').toLowerCase();
        return txt.includes('sign in') || txt.includes('log in') || txt.includes('login') || txt.includes('submit');
    }) || null;
}

async function executeLoginFlow(container = document, emailInput = null, emailVal = '', passInput = null, passVal = '') {
    const hostname = (typeof window !== 'undefined' && window.location) ? window.location.hostname : 'site';

    if (emailInput && emailVal) {
        await simulateHumanTyping(emailInput, emailVal);
        highlightField(emailInput);
    }
    await new Promise(r => setTimeout(r, 200));

    if (passInput && passVal) {
        await simulateHumanTyping(passInput, passVal);
        highlightField(passInput);
    }

    executeConsentAutoCheck(container);
    await new Promise(r => setTimeout(r, 800)); // Wait for React state to settle

    const realBtn = container.querySelector('[data-automation-id="signInSubmitButton"], [data-automation-id="signInButton"]');
    const shieldBtn = container.querySelector('[data-automation-id="click_filter"]');
    const loginBtn = realBtn || shieldBtn || findLoginSubmitButton(container);

    if (loginBtn) {
        showToast(`🔑 Signing into ${hostname}...`, "success");
        loginBtn.click();
        try {
            loginBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
        } catch (e) {}
    } else {
        showToast(`⚠️ Filled credentials, but could not locate Sign In submit button.`, "info");
    }
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

    console.log(`[v1.17.42] Auth Detection: visiblePasswords=${passwordInputCount}, isCreateAccountMode=${isCreateAccountMode}`);

    return {
        isCreateAccountMode,
        passwordInputCount,
        strictConfirmPassEl,
        visiblePasswordInputs
    };
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { executeMasterAction, executeLoginFlow, simulateHumanTyping, isElementVisible };
}
