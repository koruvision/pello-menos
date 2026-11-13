() => {
  function setInput(name, value) {
    for (const el of document.querySelectorAll('[name="' + name + '"]')) {
      if (el.type === 'checkbox' || el.type === 'radio') continue;
      el.removeAttribute('readonly');
      el.removeAttribute('disabled');
      el.focus();
      el.value = value;
      ['input', 'change', 'keyup', 'blur'].forEach((ev) => el.dispatchEvent(new Event(ev, { bubbles: true })));
    }
  }
  function setSelect(name, prefer) {
    for (const el of document.querySelectorAll('select[name="' + name + '"]')) {
      el.removeAttribute('disabled');
      let opt = null;
      if (prefer) {
        opt = Array.from(el.options).find((o) => o.value === prefer || o.textContent.trim() === prefer);
      }
      if (!opt) {
        opt = Array.from(el.options).find((o) => o.value && !/selecione/i.test(o.textContent || ''));
      }
      if (!opt) return false;
      el.selectedIndex = opt.index;
      el.value = opt.value;
      el.classList.remove('wpcf7-not-valid', 'first_null');
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }
    return true;
  }
  return { setInput, setSelect };
}
