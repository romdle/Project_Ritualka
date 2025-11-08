(function(){
  function $(selector, root=document){
    return root.querySelector(selector);
  }
  function $$(selector, root=document){
    return Array.from(root.querySelectorAll(selector));
  }

  document.addEventListener('DOMContentLoaded', () => {
    const page = document.querySelector('[data-catalog-page]');
    if(!page){
      return;
    }
    const form = document.getElementById('catalog-filters-form');
    const sidebar = page.querySelector('[data-catalog-sidebar]');
    const overlay = page.querySelector('[data-catalog-overlay]');
    const overlayContent = overlay?.querySelector('[data-catalog-overlay-content]');
    const openButton = page.querySelector('[data-filter-open]');
    const closeButtons = page.querySelectorAll('[data-filter-close]');
    const desktopMedia = window.matchMedia('(min-width: 961px)');

    if(!form){
      return;
    }

    const categoryInput = form.elements.namedItem('category');
    const sortInput = form.elements.namedItem('sort');
    const priceFromInput = form.elements.namedItem('price_from');
    const priceToInput = form.elements.namedItem('price_to');
    const priceMin = Number(form.dataset.priceMin || '0');
    const priceMax = Number(form.dataset.priceMax || '0');

    const originalParent = form.parentElement;
    const formPlaceholder = document.createElement('div');
    formPlaceholder.setAttribute('data-form-placeholder', 'true');
    formPlaceholder.style.display = 'none';
    if(form.nextSibling){
      form.parentElement.insertBefore(formPlaceholder, form.nextSibling);
    }else if(form.parentElement){
      form.parentElement.appendChild(formPlaceholder);
    }
    const overlayTransitionFallback = 400;
    let overlayRestoreTimer = null;
    let overlayTransitionHandler = null;
    let submitAfterClose = false;
    const overlayReloadParamName = 'tm';
    let overlayReloadCounter = (() => {
      try{
        const params = new URL(window.location.href).searchParams;
        const currentValue = Number(params.get(overlayReloadParamName));
        if(Number.isFinite(currentValue) && currentValue >= 0){
          return currentValue;
        }
      }catch(err){
        // ignore
      }
      return 0;
    })();
    let overlayReloadInput = null;

    function moveFormTo(target){
      if(!target || !form){
        return;
      }
      target.appendChild(form);
    }

    function ensureFormInSidebar(){
      if(sidebar && form && !sidebar.contains(form)){
        if(formPlaceholder && formPlaceholder.parentElement === sidebar){
          sidebar.insertBefore(form, formPlaceholder);
        }else{
          sidebar.appendChild(form);
        }
      }
    }

    function clearOverlayTransitionListener(){
      if(overlay && overlayTransitionHandler){
        overlay.removeEventListener('transitionend', overlayTransitionHandler);
        overlayTransitionHandler = null;
      }
    }

    function restoreForm(){
      if(overlayRestoreTimer !== null){
        window.clearTimeout(overlayRestoreTimer);
        overlayRestoreTimer = null;
      }
      clearOverlayTransitionListener();
      if(formPlaceholder && formPlaceholder.parentElement && form){
        const targetParent = formPlaceholder.parentElement;
        if(form.parentElement !== targetParent || formPlaceholder.previousSibling !== form){
          targetParent.insertBefore(form, formPlaceholder);
        }
        return;
      }
      if(originalParent && form && form.parentElement !== originalParent){
        originalParent.appendChild(form);
      }
    }

    function isOverlayOpen(){
      return Boolean(overlay && overlay.classList.contains('is-open'));
    }

    function openOverlay(){
      if(!overlay){
        return;
      }
      if(overlayRestoreTimer !== null){
        window.clearTimeout(overlayRestoreTimer);
        overlayRestoreTimer = null;
      }
      clearOverlayTransitionListener();
      submitAfterClose = false;
      restoreForm();
      if(overlayContent){
        moveFormTo(overlayContent);
      }
      overlay.classList.add('is-open');
    }

    function closeOverlay(){
      if(!overlay){
        restoreForm();
        return;
      }
      if(!overlay.classList.contains('is-open')){
        restoreForm();
        return;
      }
      overlay.classList.remove('is-open');
      if(overlayContent){
        clearOverlayTransitionListener();
        overlayTransitionHandler = (event) => {
          if(event.target !== overlay){
            return;
          }
          overlayTransitionHandler = null;
          restoreForm();
        };
        overlay.addEventListener('transitionend', overlayTransitionHandler);
        overlayRestoreTimer = window.setTimeout(() => {
          overlayRestoreTimer = null;
          restoreForm();
        }, overlayTransitionFallback);
      }else{
        restoreForm();
      }
    }
    
    function getOverlayReloadInput(){
      if(overlayReloadInput && overlayReloadInput.isConnected){
        return overlayReloadInput;
      }
      const existing = form.querySelector(`input[name="${overlayReloadParamName}"]`);
      if(existing){
        overlayReloadInput = existing;
        return overlayReloadInput;
      }
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = overlayReloadParamName;
      form.appendChild(input);
      overlayReloadInput = input;
      return overlayReloadInput;
    }

    function handleOverlayClose(forceSubmit = false){
      const shouldSubmit = forceSubmit || submitAfterClose;
      submitAfterClose = false;
      closeOverlay();
      if(shouldSubmit){
        const reloadInput = getOverlayReloadInput();
        overlayReloadCounter += 1;
        reloadInput.value = String(overlayReloadCounter);
        form.submit();
      }
    }

    if(openButton){
      openButton.addEventListener('click', () => openOverlay());
    }
    closeButtons.forEach(button => button.addEventListener('click', () => handleOverlayClose(!desktopMedia.matches)));
    overlay?.addEventListener('click', (event) => {
      if(event.target === overlay){
        handleOverlayClose();
      }
    });

    function handleDesktopChange(event){
      if(event.matches){
        if(isOverlayOpen()){
          handleOverlayClose();
        }else{
          submitAfterClose = false;
          closeOverlay();
        }
        ensureFormInSidebar();
      }
    }

    if(typeof desktopMedia.addEventListener === 'function'){
      desktopMedia.addEventListener('change', handleDesktopChange);
    }else if(typeof desktopMedia.addListener === 'function'){
      desktopMedia.addListener(handleDesktopChange);
    }

    function normalizeCategorySelection(values){
      const list = Array.isArray(values) ? values : String(values || '').split(',');
      const result = [];
      for(const raw of list){
        const normalized = String(raw || '').trim().toLowerCase();
        if(!normalized){
          continue;
        }
        if(normalized === 'all'){
          return ['all'];
        }
        if(!result.includes(normalized)){
          result.push(normalized);
        }
      }
      if(result.length === 0){
        return ['all'];
      }
      return [result[0]];
    }

    function getSelectedCategory(){
      return normalizeCategorySelection(categoryInput?.value || '')[0];
    }

    function updateCategoryButtons(selected){
      const current = selected || getSelectedCategory();
      $$('[data-filter-category]', form).forEach(control => {
        const controlSlug = (control.getAttribute('data-filter-category') || '').toLowerCase() || 'all';
        const isActive = controlSlug === current || (controlSlug === 'all' && current === 'all');
        control.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        const container = control.closest('.catalog-category-item');
        if(container){
          container.classList.toggle('is-active', isActive);
        }
      });
    }

    function writeCategorySelection(values){
      if(!categoryInput){
        return false;
      }
      const normalized = normalizeCategorySelection(values);
      const nextValue = normalized[0];
      const currentValue = getSelectedCategory();
      if(nextValue === currentValue){
        return false;
      }
      categoryInput.value = nextValue;
      return true;
    }

    function submitWithUpdates(updates){
      let hasChanges = false;
      if(categoryInput){
        if(updates.categories !== undefined){
          const normalized = normalizeCategorySelection(updates.categories);
          hasChanges = writeCategorySelection(normalized) || hasChanges;
          updateCategoryButtons(normalized[0]);
        }else if(updates.category !== undefined){
          const normalized = normalizeCategorySelection(updates.category);
          hasChanges = writeCategorySelection(normalized) || hasChanges;
          updateCategoryButtons(normalized[0]);
        }
      }
      if(sortInput && updates.sort !== undefined){
        const nextSort = String(updates.sort);
        if(sortInput.value !== nextSort){
          sortInput.value = nextSort;
          hasChanges = true;
        }
      }
      if(priceFromInput && updates.priceFrom !== undefined){
        const nextFrom = String(updates.priceFrom);
        if(priceFromInput.value !== nextFrom){
          priceFromInput.value = nextFrom;
          hasChanges = true;
        }
      }
      if(priceToInput && updates.priceTo !== undefined){
        const nextTo = String(updates.priceTo);
        if(priceToInput.value !== nextTo){
          priceToInput.value = nextTo;
          hasChanges = true;
        }
      }
      if(!hasChanges){
        return false;
      }
      submitAfterClose = false;
      form.submit();
      return true;
    }

    $$('[data-filter-category]', form).forEach(button => {
      button.addEventListener('click', () => {
        const slug = (button.getAttribute('data-filter-category') || '').toLowerCase();
        const current = getSelectedCategory();
        let next = 'all';
        if(slug && slug !== 'all' && slug !== current){
          next = slug;
        }else if(slug && slug !== 'all' && slug === current){
          next = 'all';
        }
        updateCategoryButtons(next);
        submitWithUpdates({ category: next });
      });
    });

    updateCategoryButtons();

    $$('[data-filter-sort]', form).forEach(button => {
      button.addEventListener('click', () => {
        const value = button.getAttribute('data-filter-sort') || 'price-asc';
        $$('[data-filter-sort]', form).forEach(control => {
          const isActive = control === button;
          control.classList.toggle('is-active', isActive);
          control.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });
        submitWithUpdates({ sort: value });
      });
    });

    const priceFields = {
      from: form.querySelector('[data-price-field="from"]'),
      to: form.querySelector('[data-price-field="to"]'),
    };
    const slider = form.querySelector('[data-price-slider]');

    function setPriceFields(fromValue, toValue){
      const safeFrom = Number.isFinite(fromValue) ? fromValue : priceMin;
      const safeTo = Number.isFinite(toValue) ? toValue : priceMax;
      if(priceFields.from){
        priceFields.from.value = String(Math.round(safeFrom));
      }
      if(priceFields.to){
        priceFields.to.value = String(Math.round(safeTo));
      }
    }

    if(slider){
      const inputFrom = slider.querySelector('[data-price-input="from"]');
      const inputTo = slider.querySelector('[data-price-input="to"]');
      if(inputFrom && inputTo && !inputFrom.disabled && !inputTo.disabled){
        const min = Number(inputFrom.min || priceMin);
        const max = Number(inputFrom.max || priceMax);
        const step = Math.max(Number(inputFrom.step || '1') || 1, 1);

        function setActiveHandle(handle){
          if(!inputFrom || !inputTo){
            return;
          }
          if(handle === 'from'){
            inputFrom.style.zIndex = '4';
            inputTo.style.zIndex = '3';
          }else{
            inputFrom.style.zIndex = '3';
            inputTo.style.zIndex = '4';
          }
        }

        function bindHandleActivation(element, handle){
          if(!element){
            return;
          }
          const activate = () => setActiveHandle(handle);
          if(window.PointerEvent){
            element.addEventListener('pointerdown', activate);
          }else{
            element.addEventListener('mousedown', activate);
            element.addEventListener('touchstart', activate, { passive: true });
          }
          element.addEventListener('focus', activate);
        }

        bindHandleActivation(inputFrom, 'from');
        bindHandleActivation(inputTo, 'to');

        function clampValue(value){
          if(!Number.isFinite(value)){
            return null;
          }
          const snapped = Math.round(value / step) * step;
          return Math.min(Math.max(snapped, min), max);
        }

        function applyValues(fromValue, toValue, origin){
          let nextFrom = clampValue(fromValue);
          let nextTo = clampValue(toValue);
          if(nextFrom === null){
            nextFrom = min;
          }
          if(nextTo === null){
            nextTo = max;
          }
          if(nextFrom > nextTo){
            if(origin === 'from' || origin === 'fromField'){
              nextTo = nextFrom;
            }else{
              nextFrom = nextTo;
            }
          }
          inputFrom.value = String(nextFrom);
          inputTo.value = String(nextTo);
          slider.style.setProperty('--range-from', String(nextFrom));
          slider.style.setProperty('--range-to', String(nextTo));
          setPriceFields(nextFrom, nextTo);
          return { from: nextFrom, to: nextTo };
        }

        function syncFromSlider(event){
          const origin = event?.target === inputFrom ? 'from' : 'to';
          applyValues(Number(inputFrom.value), Number(inputTo.value), origin);
        }

        function commitValues(origin){
          const values = applyValues(Number(inputFrom.value), Number(inputTo.value), origin);
          submitWithUpdates({ priceFrom: values.from, priceTo: values.to });
        }

        inputFrom.addEventListener('input', syncFromSlider);
        inputTo.addEventListener('input', syncFromSlider);
        inputFrom.addEventListener('change', () => commitValues('from'));
        inputTo.addEventListener('change', () => commitValues('to'));

        setActiveHandle('to');

        if(priceFields.from){
          priceFields.from.addEventListener('change', () => {
            const values = applyValues(Number(priceFields.from.value), Number(priceFields.to?.value ?? priceFields.from.value), 'fromField');
            submitWithUpdates({ priceFrom: values.from, priceTo: values.to });
          });
        }
        if(priceFields.to){
          priceFields.to.addEventListener('change', () => {
            const values = applyValues(Number(priceFields.from?.value ?? priceFields.to.value), Number(priceFields.to.value), 'toField');
            submitWithUpdates({ priceFrom: values.from, priceTo: values.to });
          });
        }
        slider.style.setProperty('--range-min', String(min));
        slider.style.setProperty('--range-max', String(max));
        applyValues(Number(inputFrom.value), Number(inputTo.value));
      }else{
        setPriceFields(priceMin, priceMax);
      }
    }

    const resetButton = form.querySelector('[data-filter-reset]');
    if(resetButton){
      resetButton.addEventListener('click', () => {
        const defaults = {
          category: 'all',
          sort: 'price-asc',
          priceFrom: priceMin,
          priceTo: priceMax,
        };
        if(slider){
          const inputFrom = slider.querySelector('[data-price-input="from"]');
          const inputTo = slider.querySelector('[data-price-input="to"]');
          if(inputFrom && inputTo && !inputFrom.disabled && !inputTo.disabled){
            inputFrom.value = String(priceMin);
            inputTo.value = String(priceMax);
            slider.style.setProperty('--range-from', String(priceMin));
            slider.style.setProperty('--range-to', String(priceMax));
            setPriceFields(priceMin, priceMax);
          }
        }
        setPriceFields(priceMin, priceMax);
        updateCategoryButtons('all');
        $$('[data-filter-sort]', form).forEach(control => {
          const isActive = (control.getAttribute('data-filter-sort') || '') === defaults.sort;
          control.classList.toggle('is-active', isActive);
          control.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });
        submitWithUpdates(defaults);
      });
    }

    ensureFormInSidebar();
  });
})();