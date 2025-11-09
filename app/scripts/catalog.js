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
    const sortOverlay = page.querySelector('[data-sort-overlay]');
    const filterOpenButton = page.querySelector('[data-filter-open]');
    const sortOpenButton = page.querySelector('[data-sort-open]');
    const filterCloseButtons = page.querySelectorAll('[data-filter-close]');
    const sortCloseButtons = sortOverlay ? sortOverlay.querySelectorAll('[data-sort-close]') : [];
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
    const sortControls = $$('[data-filter-sort]');

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

    function submitOverlayReloadForm(){
      const reloadInput = getOverlayReloadInput();
      overlayReloadCounter += 1;
      reloadInput.value = String(overlayReloadCounter);
      form.submit();
    }

    function handleOverlayClose(forceSubmit = false){
      const shouldSubmit = forceSubmit || submitAfterClose;
      submitAfterClose = false;
      closeOverlay();
      if(shouldSubmit){
        submitOverlayReloadForm();
      }
    }

    function isSortOverlayOpen(){
      return Boolean(sortOverlay && sortOverlay.classList.contains('is-open'));
    }

    function openSortOverlay(){
      if(!sortOverlay){
        return;
      }
      sortOverlay.classList.add('is-open');
    }

    function closeSortOverlay(){
      if(!sortOverlay){
        return;
      }
      sortOverlay.classList.remove('is-open');
    }

    function handleSortOverlayClose(forceSubmit = false){
      closeSortOverlay();
      if(forceSubmit){
        submitOverlayReloadForm();
      }
    }

    if(filterOpenButton){
      filterOpenButton.addEventListener('click', () => openOverlay());
    }
    filterCloseButtons.forEach(button => button.addEventListener('click', () => handleOverlayClose(!desktopMedia.matches)));
    overlay?.addEventListener('click', (event) => {
      if(event.target === overlay){
        handleOverlayClose();
      }
    });

    if(sortOpenButton){
      sortOpenButton.addEventListener('click', () => openSortOverlay());
    }
    sortCloseButtons.forEach(button => button.addEventListener('click', () => handleSortOverlayClose(!desktopMedia.matches)));
    sortOverlay?.addEventListener('click', (event) => {
      if(event.target === sortOverlay){
        handleSortOverlayClose();
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
        if(isSortOverlayOpen()){
          handleSortOverlayClose();
        }else{
          closeSortOverlay();
        }
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

    function updateSortControls(activeValue){
      const target = String(activeValue || '');
      sortControls.forEach(control => {
        const controlValue = control.getAttribute('data-filter-sort') || '';
        const isActive = controlValue === target;
        control.classList.toggle('is-active', isActive);
        control.setAttribute('aria-pressed', isActive ? 'true' : 'false');
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
        updateSortControls(nextSort);
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

    updateSortControls(sortInput?.value || '');

    sortControls.forEach(button => {
      button.addEventListener('click', () => {
        const value = button.getAttribute('data-filter-sort') || 'price-asc';
        const changed = submitWithUpdates({ sort: value });
        if(button.closest('[data-sort-overlay]')){
          handleSortOverlayClose(changed ? false : !desktopMedia.matches);
        }
      });
    });

    const priceFields = {
      from: form.querySelector('[data-price-field="from"]'),
      to: form.querySelector('[data-price-field="to"]'),
    };

    const priceSlider = {
      container: form.querySelector('[data-price-slider]'),
      from: form.querySelector('[data-price-slider-input="from"]'),
      to: form.querySelector('[data-price-slider-input="to"]'),
      range: form.querySelector('[data-price-slider-range]'),
      values: {
        from: form.querySelector('[data-price-slider-value="from"]'),
        to: form.querySelector('[data-price-slider-value="to"]'),
      },
    };
    
    const hasValidPriceRange = Number.isFinite(priceMax) && Number.isFinite(priceMin) && priceMax > priceMin;

    if(priceSlider.container){
      priceSlider.container.classList.toggle('is-disabled', !hasValidPriceRange);
      priceSlider.container.setAttribute('aria-hidden', hasValidPriceRange ? 'false' : 'true');
    }

    function clampPriceValue(value, fallback){
      if(!Number.isFinite(value)){
        return fallback;
      }
      if(!hasValidPriceRange){
        return fallback;
      }
      const rounded = Math.round(value);
      return Math.min(Math.max(rounded, priceMin), priceMax);
    }

    function formatPrice(value){
      if(!Number.isFinite(value)){
        return '';
      }
      try{
        return new Intl.NumberFormat('ru-RU').format(value);
      }catch(err){
        return String(value);
      }
    }

    function updateSliderRange(values){
      if(!priceSlider.range || !hasValidPriceRange){
        if(priceSlider.range){
          priceSlider.range.style.setProperty('--range-start', '0%');
          priceSlider.range.style.setProperty('--range-end', '0%');
        }
        return;
      }
      const total = priceMax - priceMin;
      const startPercent = ((values.from - priceMin) / total) * 100;
      const endPercent = ((values.to - priceMin) / total) * 100;
      const clampedStart = Math.max(0, Math.min(100, startPercent));
      const clampedEnd = Math.max(0, Math.min(100, endPercent));
      priceSlider.range.style.setProperty('--range-start', `${clampedStart}%`);
      priceSlider.range.style.setProperty('--range-end', `${Math.max(clampedStart, clampedEnd)}%`);
    }

    function updateSliderValues(values){
      if(priceSlider.values.from){
        priceSlider.values.from.textContent = formatPrice(values.from);
      }
      if(priceSlider.values.to){
        priceSlider.values.to.textContent = formatPrice(values.to);
      }
    }

    function applyPriceValues(fromValue, toValue, origin = 'to'){
      if(!hasValidPriceRange){
        const base = Number.isFinite(priceMin) ? priceMin : 0;
        if(priceFields.from){
          priceFields.from.value = String(base);
        }
        if(priceFields.to){
          priceFields.to.value = String(base);
        }
        if(priceSlider.from){
          priceSlider.from.value = String(base);
        }
        if(priceSlider.to){
          priceSlider.to.value = String(base);
        }
        updateSliderRange({ from: base, to: base });
        updateSliderValues({ from: base, to: base });        
        return { from: base, to: base };
      }

      let nextFrom = clampPriceValue(fromValue, priceMin);
      let nextTo = clampPriceValue(toValue, priceMax);

      if(nextFrom > nextTo){
        if(origin === 'from'){
          nextTo = nextFrom;
        }else{
          nextFrom = nextTo;
        }
      }

      if(priceFields.from){
        priceFields.from.value = String(nextFrom);
      }
      if(priceFields.to){
        priceFields.to.value = String(nextTo);
      }

      if(priceSlider.from){
        priceSlider.from.value = String(nextFrom);
      }
      if(priceSlider.to){
        priceSlider.to.value = String(nextTo);
      }

      updateSliderRange({ from: nextFrom, to: nextTo });
      updateSliderValues({ from: nextFrom, to: nextTo });
      
      return { from: nextFrom, to: nextTo };
    }

    function setPriceFields(fromValue, toValue){
      return applyPriceValues(fromValue, toValue);
    }

    setPriceFields(Number(priceFields.from?.value), Number(priceFields.to?.value));

    if(priceFields.from && !priceFields.from.disabled){
      priceFields.from.addEventListener('change', () => {
        const values = applyPriceValues(
          Number(priceFields.from.value),
          Number(priceFields.to?.value ?? priceFields.from.value),
          'from',
        );
        submitWithUpdates({ priceFrom: values.from, priceTo: values.to });
      });
    }

    if(priceFields.to && !priceFields.to.disabled){
      priceFields.to.addEventListener('change', () => {
        const values = applyPriceValues(
          Number(priceFields.from?.value ?? priceFields.to.value),
          Number(priceFields.to.value),
          'to',
        );
        submitWithUpdates({ priceFrom: values.from, priceTo: values.to });
      });
    }

    function handleSliderUpdate(origin, submit){
      const fromValue = Number(priceSlider.from?.value ?? priceMin);
      const toValue = Number(priceSlider.to?.value ?? priceMax);
      const values = applyPriceValues(fromValue, toValue, origin);
      if(submit){
        submitWithUpdates({ priceFrom: values.from, priceTo: values.to });
      }
    }

    if(priceSlider.from && !priceSlider.from.disabled){
      priceSlider.from.addEventListener('input', () => handleSliderUpdate('from', false));
      priceSlider.from.addEventListener('change', () => handleSliderUpdate('from', true));
    }

    if(priceSlider.to && !priceSlider.to.disabled){
      priceSlider.to.addEventListener('input', () => handleSliderUpdate('to', false));
      priceSlider.to.addEventListener('change', () => handleSliderUpdate('to', true));
    }

    const resetButton = form.querySelector('[data-filter-reset]');
    if(resetButton){
      resetButton.addEventListener('click', () => {
        const defaults = {
          category: 'all',
          sort: 'price-asc',
          priceFrom: priceMin,
          priceTo: hasValidPriceRange ? priceMax : priceMin,
        };
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