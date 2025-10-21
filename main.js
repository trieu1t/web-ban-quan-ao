console.log('Shop frontend loaded');

async function addToCart(pid){
  try{
    const res = await fetch('/cart/add/'+pid, {method:'POST'});
    const j = await res.json();
    if(j.ok){
      const el = document.querySelector('#cart-count');
      if(el) el.textContent = j.cart_count;
      alert('Đã thêm 1 sản phẩm vào giỏ');
    } else {
      alert('Không thêm được vào giỏ');
    }
  }catch(err){
    console.error(err); alert('Lỗi mạng');
  }
}

document.addEventListener('click', function(e){
  const t = e.target;
  if(t && t.classList.contains('add-to-cart')){
    const pid = t.dataset.id;
    addToCart(pid);
  }
});

// update quantities on cart page
document.addEventListener('change', function(e){
  const t = e.target;
  if(t && t.classList.contains('qty-input')){
    const id = t.dataset.id;
    const val = parseInt(t.value) || 0;
    fetch('/cart/update', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({[id]: val})
    }).then(()=> location.reload());
  }
});


// Lazy-load images with IntersectionObserver and reveal animation
function initLazyImages(){
  const imgs = document.querySelectorAll('img.lazy-img');
  if('IntersectionObserver' in window){
    const io = new IntersectionObserver((entries, observer)=>{
      entries.forEach(ent=>{
        if(ent.isIntersecting){
          const img = ent.target;
          const src = img.dataset.src;
          if(src){ img.src = src; }
          img.addEventListener('load', ()=> img.classList.add('visible'));
          observer.unobserve(img);
        }
      });
    }, {rootMargin: '50px 0px'});
    imgs.forEach(i=> io.observe(i));
  } else {
    // fallback: load all
    imgs.forEach(img=>{ img.src = img.dataset.src; img.classList.add('visible'); });
  }
}

document.addEventListener('DOMContentLoaded', initLazyImages);