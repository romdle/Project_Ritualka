(function(){
  document.addEventListener('DOMContentLoaded', () => {
    const wrappers = document.querySelectorAll('[data-product-image]');
    if(!wrappers.length){
      return;
    }
    wrappers.forEach(wrapper => {
      const img = wrapper.querySelector('[data-product-image-source]') || wrapper.querySelector('img');
      if(!img){
        return;
      }
      wrapper.style.cursor = 'zoom-in';
      wrapper.addEventListener('click', () => {
        const src = img.getAttribute('src');
        if(src){
          window.RitualkaCommon?.showProductImage?.(src, img.getAttribute('alt') || '');
        }
      });
    });
  });
})();