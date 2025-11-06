(function(){
  function $(selector, root=document){
    return root.querySelector(selector);
  }
  function $$(selector, root=document){
    return Array.from(root.querySelectorAll(selector));
  }

  function formatNumber(value){
    const num = Number(value);
    if(!Number.isFinite(num)){
      return '0';
    }
    return num.toLocaleString('ru-RU');
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

    let originalParent = form.parentElement;

    function moveFormTo(target){
      if(!target || !form){
        return;
      }
      target.appendChild(form);
    }

    function ensureFormInSidebar(){
      if(sidebar && form && !sidebar.contains(form)){
        sidebar.appendChild(form);
      }
    }

    function openOverlay(){
      if(!overlay){
        return;
      }
      if(overlayContent){
        moveFormTo(overlayContent);
      }
      overlay.classList.add('is-open');
    }

    function closeOverlay(){
      if(!overlay){
        return;
      }
      overlay.classList.remove('is-open');
      if(originalParent){
        moveFormTo(originalParent);
      }
    }

    if(openButton){
      openButton.addEventListener('click', () => openOverlay());
    }
    closeButtons.forEach(button => button.addEventListener('click', () => closeOverlay()));
    overlay?.addEventListener('click', (event) => {
      if(event.target === overlay){
        closeOverlay();
      }
    });

    function handleDesktopChange(event){
      if(event.matches){
        closeOverlay();
        ensureFormInSidebar();
      }
    }

    if(typeof desktopMedia.addEventListener === 'function'){
      desktopMedia.addEventListener('change', handleDesktopChange);
    }else if(typeof desktopMedia.addListener === 'function'){
      desktopMedia.addListener(handleDesktopChange);
    }

    function submitWithUpdates(updates){
      if(categoryInput && updates.category !== undefined){
        categoryInput.value = updates.category;
      }
      if(sortInput && updates.sort !== undefined){
        sortInput.value = updates.sort;
      }
      if(priceFromInput && updates.priceFrom !== undefined){
        priceFromInput.value = String(updates.priceFrom);
      }
      if(priceToInput && updates.priceTo !== undefined){
        priceToInput.value = String(updates.priceTo);
      }
      closeOverlay();
      form.submit();
    }

    $$('[data-filter-category]', form).forEach(button => {
      button.addEventListener('click', () => {
        const value = button.getAttribute('data-filter-category') || 'all';
        submitWithUpdates({ category: value });
      });
    });

    $$('[data-filter-sort]', form).forEach(button => {
      button.addEventListener('click', () => {
        const value = button.getAttribute('data-filter-sort') || 'price-asc';
        submitWithUpdates({ sort: value });
      });
    });

    const priceLabels = form.querySelectorAll('.catalog-price-values strong');
    const slider = form.querySelector('[data-price-slider]');

    function updatePriceLabels(fromValue, toValue){
      if(priceLabels[0]){
        priceLabels[0].textContent = `${formatNumber(fromValue)} ₽`;
      }
      if(priceLabels[1]){
        priceLabels[1].textContent = `${formatNumber(toValue)} ₽`;
      }
    }

    if(slider){
      const inputFrom = slider.querySelector('[data-price-input="from"]');
      const inputTo = slider.querySelector('[data-price-input="to"]');
      if(inputFrom && inputTo && !inputFrom.disabled && !inputTo.disabled){
        const min = Number(inputFrom.min || priceMin);
        const max = Number(inputFrom.max || priceMax);

        function syncInputs(event){
          let fromValue = Number(inputFrom.value);
          let toValue = Number(inputTo.value);
          if(fromValue > toValue){
            if(event?.target === inputFrom){
              toValue = fromValue;
              inputTo.value = String(toValue);
            }else{
              fromValue = toValue;
              inputFrom.value = String(fromValue);
            }
          }
          slider.style.setProperty('--range-from', String(fromValue));
          slider.style.setProperty('--range-to', String(toValue));
          updatePriceLabels(fromValue, toValue);
        }

        function commit(){
          const fromValue = Number(inputFrom.value);
          const toValue = Number(inputTo.value);
          submitWithUpdates({ priceFrom: fromValue, priceTo: toValue });
        }

        inputFrom.addEventListener('input', syncInputs);
        inputTo.addEventListener('input', syncInputs);
        inputFrom.addEventListener('change', commit);
        inputTo.addEventListener('change', commit);
        slider.style.setProperty('--range-min', String(min));
        slider.style.setProperty('--range-max', String(max));
        syncInputs();
      }else{
        updatePriceLabels(priceMin, priceMax);
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
            updatePriceLabels(priceMin, priceMax);
          }
        }
        submitWithUpdates(defaults);
      });
    }

    ensureFormInSidebar();
  });
})();