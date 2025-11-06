(function(){
  const $ = (selector, root=document) => root.querySelector(selector);
  const $$ = (selector, root=document) => Array.from(root.querySelectorAll(selector));

  function setCurrentYear(){
    const node = $('#year');
    if(node){
      node.textContent = String(new Date().getFullYear());
    }
  }

  function initMenu(){
    const toggle = $('#menu-toggle-button');
    const menu = $('#mobile-menu');
    if(!toggle || !menu){
      return;
    }

    const body = document.body;

    function computeMenuHeight(){
      const inner = menu.querySelector('.mobile-menu__inner');
      return inner ? inner.scrollHeight : 0;
    }

    function applyMenuHeight(){
      if(menu.classList.contains('is-open')){
        const height = computeMenuHeight();
        if(height){
          menu.style.setProperty('--menu-height', `${height}px`);
        }
      }
    }

    function setOpen(force){
      const shouldOpen = force !== undefined ? force : !menu.classList.contains('is-open');
      menu.classList.toggle('is-open', shouldOpen);
      toggle.classList.toggle('is-active', shouldOpen);
      toggle.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
      menu.setAttribute('aria-hidden', shouldOpen ? 'false' : 'true');
      body.classList.toggle('menu-open', shouldOpen);
      if(shouldOpen){
        requestAnimationFrame(applyMenuHeight);
      }
    }

    toggle.addEventListener('click', () => setOpen());
    menu.addEventListener('click', (event) => {
      if(event.target === menu){
        setOpen(false);
      }
    });
    document.addEventListener('keydown', (event) => {
      if(event.key === 'Escape' && menu.classList.contains('is-open')){
        setOpen(false);
      }
    });
    window.addEventListener('resize', applyMenuHeight);

    $$('.mobile-menu__nav a', menu).forEach(link => {
      link.addEventListener('click', () => setOpen(false));
    });
  }

  function normalizeDigits(value){
    return (value || '').replace(/\D+/g, '');
  }

  function formatPhone(value){
    if(!value){
      return '';
    }
    let digits = value;
    if(digits[0] === '8'){
      digits = '7' + digits.slice(1);
    }
    if(digits[0] !== '7'){
      digits = '7' + digits;
    }
    digits = digits.slice(0, 11);
    let result = '+7 ';
    if(digits.length > 1){
      result += '(' + digits.slice(1, 4);
      if(digits.length >= 4){
        result += ') ';
      }
    }
    if(digits.length >= 7){
      result += digits.slice(4, 7) + '-' + digits.slice(7, 9) + '-' + digits.slice(9, 11);
    }else if(digits.length > 4){
      result += digits.slice(4);
    }
    return result.trim();
  }

  function initCallbackForm(){
    const modal = $('#modal-backdrop');
    const form = $('#callback-form');
    const success = $('#success');
    const btnClose = $('#close-btn');
    const submitBtn = $('#submit-btn');
    const phone = $('#phone');
    const nameInput = $('#name');

    if(!modal || !form || !success || !submitBtn || !phone || !nameInput){
      return;
    }

    function open(prefill){
      success.style.display = 'none';
      form.reset();
      if(prefill){
        $('#comment').value = prefill;
      }
      modal.style.display = 'flex';
      modal.setAttribute('aria-hidden', 'false');
      nameInput.focus();
    }

    function close(){
      modal.style.display = 'none';
      modal.setAttribute('aria-hidden', 'true');
    }

    phone.addEventListener('input', () => {
      const digits = normalizeDigits(phone.value);
      phone.value = formatPhone(digits);
    });
    phone.addEventListener('focus', () => {
      if(!phone.value){
        phone.value = '+7 (';
      }
    });

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const name = nameInput.value.trim();
      const digits = normalizeDigits(phone.value);
      let valid = true;
      const errName = $('#err-name');
      const errPhone = $('#err-phone');
      if(name.length < 2){
        valid = false;
        if(errName) errName.style.display = 'block';
      }else if(errName){
        errName.style.display = 'none';
      }
      if(!(digits.length === 11 && digits[0] === '7')){
        valid = false;
        if(errPhone) errPhone.style.display = 'block';
      }else if(errPhone){
        errPhone.style.display = 'none';
      }
      if(!valid){
        return;
      }
      submitBtn.disabled = true;
      submitBtn.textContent = 'Отправка...';
      setTimeout(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Отправить';
        success.style.display = 'block';
        setTimeout(close, 1200);
      }, 700);
    });

    btnClose?.addEventListener('click', close);
    modal.addEventListener('click', (event) => {
      if(event.target === modal){
        close();
      }
    });
    document.addEventListener('keydown', (event) => {
      if(event.key === 'Escape' && modal.getAttribute('aria-hidden') === 'false'){
        close();
      }
    });

    $$('[data-action="callback"]').forEach(button => {
      button.addEventListener('click', () => {
        const prefill = button.getAttribute('data-prefill') || '';
        open(prefill);
      });
    });

    window.RitualkaCommon = window.RitualkaCommon || {};
    window.RitualkaCommon.openCallback = open;
    window.RitualkaCommon.closeCallback = close;
  }

  function setupProductOverlay(){
    const overlay = $('[data-product-image-overlay]');
    if(!overlay){
      return;
    }
    const overlayImage = overlay.querySelector('[data-product-image-overlay-image]');
    if(!overlayImage){
      return;
    }

    function clearOverlay(){
      overlay.classList.remove('is-visible');
      overlay.setAttribute('hidden', '');
      overlayImage.removeAttribute('src');
      overlayImage.removeAttribute('alt');
    }

    overlay.addEventListener('click', (event) => {
      if(event.target === overlay){
        clearOverlay();
      }
    });
    document.addEventListener('keydown', (event) => {
      if(event.key === 'Escape' && overlay.classList.contains('is-visible')){
        clearOverlay();
      }
    });

    window.RitualkaCommon = window.RitualkaCommon || {};
    window.RitualkaCommon.showProductImage = (src, alt='') => {
      if(!src){
        return;
      }
      overlayImage.setAttribute('src', src);
      if(alt){
        overlayImage.setAttribute('alt', alt);
      }
      overlay.classList.add('is-visible');
      overlay.removeAttribute('hidden');
    };
    window.RitualkaCommon.hideProductImage = clearOverlay;
  }

  function setupCarousels(root=document){
    const instances = [];
    const mediaQuery = window.matchMedia('(pointer: coarse) and (max-width: 960px)');

    function setupCarousel(carousel){
      if(carousel.__initialized){
        return;
      }
      const viewport = carousel.querySelector('.product-carousel-viewport');
      const track = carousel.querySelector('.product-carousel-track');
      const prev = carousel.querySelector('[data-carousel-prev]');
      const next = carousel.querySelector('[data-carousel-next]');
      if(!viewport || !track){
        return;
      }
      let index = 0;
      let touchMode = mediaQuery.matches;

      function totalItems(){
        return track.querySelectorAll('.product-tile').length;
      }

      function gapSize(){
        const style = window.getComputedStyle(track);
        const gap = parseFloat(style.columnGap || style.gap || '0');
        return Number.isFinite(gap) ? gap : 0;
      }

      function measureOverflow(){
        return track.scrollWidth > track.clientWidth + 2;
      }

      function computeVisible(){
        const card = track.querySelector('.product-tile');
        if(!card){
          return 1;
        }
        const cardWidth = card.getBoundingClientRect().width;
        if(cardWidth <= 0){
          return 1;
        }
        const viewportWidth = viewport.getBoundingClientRect().width;
        const gap = gapSize();
        const approx = Math.floor((viewportWidth + gap) / (cardWidth + gap));
        return Math.max(1, Math.min(totalItems(), approx || 1));
      }

      function updateButtons(maxIndex, hasOverflow){
        const hideButtons = touchMode;
        const effectiveOverflow = hideButtons ? measureOverflow() : hasOverflow;
        carousel.classList.toggle('is-scrollable', !hideButtons && effectiveOverflow);
        if(prev){
          const disabled = hideButtons || index <= 0;
          prev.disabled = disabled;
          prev.setAttribute('aria-disabled', disabled ? 'true' : 'false');
          prev.style.visibility = (!hideButtons && effectiveOverflow) ? 'visible' : 'hidden';
        }
        if(next){
          const disabled = hideButtons || index >= maxIndex;
          next.disabled = disabled;
          next.setAttribute('aria-disabled', disabled ? 'true' : 'false');
          next.style.visibility = (!hideButtons && effectiveOverflow) ? 'visible' : 'hidden';
        }
      }

      function applyTransform(){
        if(touchMode){
          track.style.transform = '';
          return;
        }
        const card = track.querySelector('.product-tile');
        if(!card){
          track.style.transform = 'translateX(0)';
          return;
        }
        const offset = index * (card.getBoundingClientRect().width + gapSize());
        track.style.transform = `translateX(${-offset}px)`;
      }

      function slideTo(target){
        touchMode = mediaQuery.matches;
        if(touchMode){
          updateButtons(0, measureOverflow());
          track.style.transform = '';
          return;
        }
        const visible = computeVisible();
        const maxIndex = Math.max(0, totalItems() - visible);
        index = Math.max(0, Math.min(target, maxIndex));
        applyTransform();
        updateButtons(maxIndex, totalItems() > visible);
      }

      function slideBy(delta){
        slideTo(index + delta);
      }

      prev?.addEventListener('click', () => slideBy(-1));
      next?.addEventListener('click', () => slideBy(1));

      function handleMediaChange(){
        touchMode = mediaQuery.matches;
        slideTo(index);
      }

      if(typeof mediaQuery.addEventListener === 'function'){
        mediaQuery.addEventListener('change', handleMediaChange);
      }else if(typeof mediaQuery.addListener === 'function'){
        mediaQuery.addListener(handleMediaChange);
      }

      window.addEventListener('resize', () => slideTo(index));

      slideTo(0);
      carousel.__initialized = true;

      instances.push({ refresh: () => slideTo(index) });
    }

    $$('[data-carousel]', root).forEach(setupCarousel);
    return instances;
  }

  function init(){
    setCurrentYear();
    initMenu();
    initCallbackForm();
    setupProductOverlay();
    const instances = setupCarousels();
    window.RitualkaCommon = window.RitualkaCommon || {};
    window.RitualkaCommon.initCarousels = setupCarousels;
    window.RitualkaCommon.carouselInstances = instances;
  }

  document.addEventListener('DOMContentLoaded', init);
})();