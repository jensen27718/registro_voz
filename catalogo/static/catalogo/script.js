document.addEventListener('DOMContentLoaded', () => {
    const MOCK_DATA = {
        tiposProducto: [
            { id: 1, nombre: 'Stickers Impresos', descripcion: 'Adhesivos de alta calidad para toda ocasión.' },
            { id: 2, nombre: 'Stickers para Cintas', descripcion: 'Ideales para marcar cintas de regalos y empaques.' },
        ],
        categorias: [
            { id: 1, tipoProductoId: 1, nombre: 'Primera Comunión', image: 'https://placehold.co/400x400/E2E8F0/333?text=Comunión' },
            { id: 2, tipoProductoId: 1, nombre: 'Cumpleaños', image: 'https://placehold.co/400x400/D1FAE5/333?text=Cumple' },
            { id: 3, tipoProductoId: 2, nombre: 'Marcas de Ropa', image: 'https://placehold.co/400x400/FEF3C7/333?text=Ropa' },
        ],
        productos: [
            { id: 101, categoriaId: 1, nombre: 'Cáliz y Hostia', image: 'https://placehold.co/600x600/E2E8F0/333?text=Cáliz' },
            { id: 201, categoriaId: 2, nombre: 'Pastel de Fiesta', image: 'https://placehold.co/600x600/D1FAE5/333?text=Pastel' },
            { id: 301, categoriaId: 3, nombre: 'Cinta Satinada Logo', image: 'https://placehold.co/600x600/FEF3C7/333?text=Cinta' },
        ],
        atributoDefs: [
            { id: 1, nombre: 'Tamaño' }, { id: 2, nombre: 'Acabado' }, { id: 3, nombre: 'Alto' },
        ],
        valorAtributos: [
            { id: 10, atributoDefId: 1, valor: 'Pequeño' }, { id: 11, atributoDefId: 1, valor: 'Mediano' },
            { id: 20, atributoDefId: 2, valor: 'Brillante' }, { id: 21, atributoDefId: 2, valor: 'Mate' },
            { id: 30, atributoDefId: 3, valor: '2cm' }, { id: 31, atributoDefId: 3, valor: '4cm' },
        ],
        variacionesProducto: [
            { id: 1001, productoId: 101, precioBase: 5000, valorAtributoIds: [10, 20] },
            { id: 1002, productoId: 101, precioBase: 5500, valorAtributoIds: [10, 21] },
            { id: 1003, productoId: 101, precioBase: 8000, valorAtributoIds: [11, 20] },
            { id: 2001, productoId: 201, precioBase: 6000, valorAtributoIds: [10] },
            { id: 2002, productoId: 201, precioBase: 9000, valorAtributoIds: [11] },
            { id: 3001, productoId: 301, precioBase: 15000, valorAtributoIds: [30] },
            { id: 3002, productoId: 301, precioBase: 25000, valorAtributoIds: [31] },
        ],
        promos: [
            { id: 1, codigo: 'BIENVENIDO10', descripcion: '10% de descuento para nuevos clientes', porcentaje: 10, fechaInicio: '2023-01-01T00:00:00Z', fechaFin: '2029-12-31T23:59:59Z', activo: true },
            { id: 2, codigo: 'OFERTAFLASH', descripcion: '25% de descuento solo por hoy', porcentaje: 25, fechaInicio: '2023-01-01T00:00:00Z', fechaFin: '2023-12-31T23:59:59Z', activo: false },
        ]
    };
    const WHATSAPP_NUMBER = '573001234567';

    let state = {
        currentUser: null,
        cart: { items: [], appliedPromoCode: null },
        navigationStack: [],
        modalSelection: { productoId: null, variation: null, quantity: 1, selectedAtributos: {} }
    };

    const pages = document.querySelectorAll('.page');
    const loginForm = document.getElementById('login-form');
    const phoneInput = document.getElementById('phone');
    const registrationFields = document.getElementById('registration-fields');
    const nameInput = document.getElementById('name');
    const addressInput = document.getElementById('address');
    const listingPage = document.getElementById('categories-page');
    const listingGrid = document.getElementById('categories-grid');
    const listingTitle = listingPage.querySelector('h2');
    const productsPage = document.getElementById('products-page');
    const productsGrid = document.getElementById('products-grid');
    const productsTitle = document.getElementById('products-title');
    const backToCategoriesBtn = document.getElementById('back-to-categories');
    const cartToggleBtn = document.getElementById('cart-toggle-btn');
    const closeCartBtn = document.getElementById('close-cart-btn');
    const cartSidebar = document.getElementById('cart-sidebar');
    const cartCount = document.getElementById('cart-count');
    const cartItemsContainer = document.getElementById('cart-items');
    const cartFooter = document.querySelector('#cart-sidebar .p-6.border-t');
    const checkoutBtn = document.getElementById('checkout-btn');
    const clearCartBtn = document.getElementById('clear-cart-btn');
    const productModal = document.getElementById('product-modal');
    const modalOverlay = document.getElementById('modal-overlay');
    const modalProductImg = document.getElementById('modal-product-img');
    const modalProductName = document.getElementById('modal-product-name');
    const modalQuantityMinus = document.getElementById('modal-quantity-minus');
    const modalQuantityPlus = document.getElementById('modal-quantity-plus');
    const modalQuantityValue = document.getElementById('modal-quantity-value');
    const modalProductAttributesContainer = document.querySelector('#product-modal .flex-grow.overflow-y-auto');
    const modalAddToCartBtn = document.getElementById('modal-add-to-cart-btn');
    const confirmationToast = document.getElementById('confirmation-toast');

    const openProductModal = (productoId) => {
        const producto = MOCK_DATA.productos.find(p => p.id === productoId);
        if (!producto) return;
        state.modalSelection = { productoId, variation: null, quantity: 1, selectedAtributos: {} };
        modalProductImg.src = producto.image;
        modalProductName.textContent = producto.name;
        const dynamicContent = modalProductAttributesContainer.querySelector('#dynamic-attributes');
        if (dynamicContent) dynamicContent.remove();
        const variaciones = MOCK_DATA.variacionesProducto.filter(v => v.productoId === productoId);
        if (variaciones.length === 0) return;
        const allValorAtributoIds = [...new Set(variaciones.flatMap(v => v.valorAtributoIds))];
        const allAtributoDefIds = [...new Set(allValorAtributoIds.map(valId => MOCK_DATA.valorAtributos.find(v => v.id === valId).atributoDefId))];
        let attributesHTML = '<div id="dynamic-attributes" class="space-y-6">';
        allAtributoDefIds.forEach(defId => {
            const atributoDef = MOCK_DATA.atributoDefs.find(def => def.id === defId);
            const valoresDisponibles = [...new Set(variaciones.flatMap(v => v.valorAtributoIds))]
                .map(valId => MOCK_DATA.valorAtributos.find(v => v.id === valId))
                .filter(val => val.atributoDefId === defId);
            let optionsHTML = valoresDisponibles.map(val => {
                if (atributoDef.nombre.toLowerCase() === 'color') {
                     return `<div class="color-swatch" data-atributo-def-id="${defId}" data-valor-id="${val.id}" style="background: ${val.display || '#ccc'};" title="${val.valor}"></div>`;
                }
                return `<div class="variation-option" data-atributo-def-id="${defId}" data-valor-id="${val.id}">${val.valor}</div>`;
            }).join('');
            attributesHTML += `
                <div>
                    <h3 class="text-xl font-bold mb-3">Elige ${atributoDef.nombre}:</h3>
                    <div class="flex flex-wrap gap-3">${optionsHTML}</div>
                </div>`;
        });
        attributesHTML += '</div>';
        modalProductAttributesContainer.querySelector('div:first-child').insertAdjacentHTML('afterend', attributesHTML);
        updateModalUI();
        modalOverlay.classList.remove('hidden');
        productModal.classList.remove('translate-y-full');
    };

    const updateModalUI = () => {
        modalQuantityValue.textContent = state.modalSelection.quantity;
        modalQuantityMinus.disabled = state.modalSelection.quantity <= 1;
        const { productoId, selectedAtributos } = state.modalSelection;
        const variacionesDisponibles = MOCK_DATA.variacionesProducto.filter(v => v.productoId === productoId);
        const totalAtributosRequeridos = [...new Set(variacionesDisponibles.flatMap(v => v.valorAtributoIds).map(valId => MOCK_DATA.valorAtributos.find(v => v.id === valId).atributoDefId))].length;
        let variation = null;
        const selectedValorIds = Object.values(selectedAtributos);
        if (selectedValorIds.length === totalAtributosRequeridos) {
            variation = variacionesDisponibles.find(v =>
                v.valorAtributoIds.length === selectedValorIds.length &&
                selectedValorIds.every(id => v.valorAtributoIds.includes(id))
            );
        }
        state.modalSelection.variation = variation || null;
        if (variation) {
            const totalPrice = variation.precioBase * state.modalSelection.quantity;
            modalAddToCartBtn.textContent = `Añadir ${state.modalSelection.quantity} - $${totalPrice.toLocaleString('es-CO')}`;
            modalAddToCartBtn.disabled = false;
        } else {
            modalAddToCartBtn.textContent = 'Completa tu selección';
            modalAddToCartBtn.disabled = true;
        }
    };

    const addToCart = () => {
        const { variation, quantity } = state.modalSelection;
        if (!variation) return;
        const existingItem = state.cart.items.find(item => item.variationId === variation.id);
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            const producto = MOCK_DATA.productos.find(p => p.id === variation.productoId);
            const atributos = variation.valorAtributoIds.map(valId => {
                const valor = MOCK_DATA.valorAtributos.find(v => v.id === valId);
                const definicion = MOCK_DATA.atributoDefs.find(d => d.id === valor.atributoDefId);
                return { nombre: definicion.nombre, valor: valor.valor };
            });
            state.cart.items.push({
                variationId: variation.id,
                productoId: producto.id,
                name: producto.name,
                image: producto.image,
                priceBase: variation.precioBase,
                quantity,
                atributos,
            });
        }
        localStorage.setItem('cart', JSON.stringify(state.cart));
        renderCart();
        closeModal();
        showConfirmationToast();
    };

    const renderCart = () => {
        const { items, appliedPromoCode } = state.cart;
        const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);
        cartCount.textContent = totalItems;
        if (totalItems > 0) {
            cartCount.classList.add('cart-bounce');
            setTimeout(() => cartCount.classList.remove('cart-bounce'), 600);
        }
        if (items.length === 0) {
            cartItemsContainer.innerHTML = `<p class="text-gray-500 text-center my-8">Tu carrito está vacío.</p>`;
            checkoutBtn.disabled = true;
        } else {
            cartItemsContainer.innerHTML = items.map(item => {
                const atributosDesc = item.atributos.map(a => a.valor).join(' / ');
                return `
                <div class="flex items-center gap-4 mb-4" data-variation-id="${item.variationId}">
                    <img src="${item.image}" alt="${item.name}" class="w-20 h-20 rounded-lg object-cover">
                    <div class="flex-grow">
                        <p class="font-bold">${item.name}</p>
                        <p class="text-sm text-gray-600">${atributosDesc}</p>
                        <p class="font-bold text-blue-600">$${(item.priceBase * item.quantity).toLocaleString('es-CO')}</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <button class="quantity-change text-lg font-bold p-2" data-change="-1">-</button>
                        <span class="font-bold w-8 text-center">${item.quantity}</span>
                        <button class="quantity-change text-lg font-bold p-2" data-change="1">+</button>
                    </div>
                </div>`;
            }).join('');
            checkoutBtn.disabled = false;
        }
        const subtotal = items.reduce((sum, item) => sum + item.priceBase * item.quantity, 0);
        let discount = 0;
        let promo = null;
        if (appliedPromoCode) {
            promo = MOCK_DATA.promos.find(p => p.codigo === appliedPromoCode);
            if (promo) discount = subtotal * (promo.porcentaje / 100);
        }
        const total = subtotal - discount;
        const totalsElement = cartFooter.querySelector('#cart-totals-summary');
        const promoElement = cartFooter.querySelector('#cart-promo-section');
        totalsElement.innerHTML = `
            <div class="flex justify-between items-center text-lg">
                <span>Subtotal:</span>
                <span class="font-semibold">$${subtotal.toLocaleString('es-CO')}</span>
            </div>
            ${promo ? `
            <div class="flex justify-between items-center text-lg text-green-600">
                <span>Descuento (${promo.porcentaje}%):</span>
                <span class="font-semibold">-$${discount.toLocaleString('es-CO')}</span>
            </div>` : ''}
            <div class="flex justify-between items-center mt-2 pt-2 border-t">
                <span class="text-xl font-bold">Total:</span>
                <span class="text-2xl font-extrabold text-gray-900">$${total.toLocaleString('es-CO')}</span>
            </div>`;
        promoElement.innerHTML = `
            ${promo ? `
            <div class="text-center text-green-600 font-bold mb-2">
                Código "${promo.codigo}" aplicado!
                <button id="remove-promo-btn" class="text-red-500 underline ml-2">(Quitar)</button>
            </div>` : `
            <div class="flex gap-2">
                <input type="text" id="promo-code-input" placeholder="Código de promo" class="w-full text-lg p-2 border border-gray-300 rounded-lg">
                <button id="apply-promo-btn" class="bg-gray-800 text-white font-bold py-2 px-4 rounded-lg">Aplicar</button>
            </div>
            <p id="promo-error" class="text-red-500 text-sm mt-1 h-4"></p>`
            }
        `;
    };

    const applyPromo = () => {
        const input = document.getElementById('promo-code-input');
        const errorP = document.getElementById('promo-error');
        const code = input.value.trim().toUpperCase();
        if (!code) return;
        const promo = MOCK_DATA.promos.find(p => p.codigo === code);
        const now = new Date();
        if (promo && promo.activo && new Date(promo.fechaInicio) <= now && new Date(promo.fechaFin) >= now) {
            state.cart.appliedPromoCode = code;
            localStorage.setItem('cart', JSON.stringify(state.cart));
            renderCart();
        } else {
            errorP.textContent = "Código inválido o expirado.";
            input.value = '';
        }
    };

    const removePromo = () => {
        state.cart.appliedPromoCode = null;
        localStorage.setItem('cart', JSON.stringify(state.cart));
        renderCart();
    };

    const handleCheckout = () => {
        if (!state.currentUser) { alert("Por favor, inicia sesión para continuar."); toggleCart(false); showPage('login-page'); return; }
        let message = `¡Hola! 👋 Quisiera hacer el siguiente pedido:\n\n`;
        const { items, appliedPromoCode } = state.cart;
        items.forEach(item => {
            const atributosDesc = item.atributos.map(a => `${a.nombre}: ${a.valor}`).join('\n  - ');
            message += `*Producto:* ${item.name}\n  - ${atributosDesc}\n  - Cantidad: ${item.quantity}\n  - Precio Base: $${(item.priceBase * item.quantity).toLocaleString('es-CO')}\n\n`;
        });
        const subtotal = items.reduce((sum, item) => sum + item.priceBase * item.quantity, 0);
        let discount = 0;
        let promo = null;
        if (appliedPromoCode) {
            promo = MOCK_DATA.promos.find(p => p.codigo === appliedPromoCode);
            if (promo) discount = subtotal * (promo.porcentaje / 100);
        }
        const total = subtotal - discount;
        message += `*Subtotal:* $${subtotal.toLocaleString('es-CO')}\n`;
        if (promo) {
            message += `*Descuento (${promo.porcentaje}%):* -$${discount.toLocaleString('es-CO')}\n`;
        }
        message += `*TOTAL DEL PEDIDO: $${total.toLocaleString('es-CO')}*\n\n`;
        message += `*Datos de Envío:*\n- Nombre: ${state.currentUser.name}\n- Dirección: ${state.currentUser.address}\n- Teléfono: ${state.currentUser.phone}\n\n¡Gracias!`;
        const whatsappUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;
        console.log("Pedido Creado (Estado: PENDIENTE):", { user: state.currentUser, cart: state.cart, total, date: new Date().toISOString() });
        window.open(whatsappUrl, '_blank');
        state.cart = { items: [], appliedPromoCode: null };
        localStorage.removeItem('cart');
        renderCart();
        toggleCart(false);
        alert('¡Gracias! Serás redirigido a WhatsApp para confirmar tu pedido.');
    };

    const showPage = (pageId) => { pages.forEach(page => page.classList.add('hidden')); document.getElementById(pageId).classList.remove('hidden'); window.scrollTo(0, 0); };
    const navigateTo = (view, contextId = null) => { state.navigationStack.push({ view, contextId }); renderCurrentView(); };
    const navigateBack = () => { if (state.navigationStack.length > 1) { state.navigationStack.pop(); renderCurrentView(); } };
    const renderCurrentView = () => { const { view, contextId } = state.navigationStack[state.navigationStack.length - 1]; backToCategoriesBtn.style.display = state.navigationStack.length > 2 ? 'block' : 'none'; switch(view) { case 'tiposProducto': renderTiposProducto(); break; case 'categorias': renderCategorias(contextId); break; case 'productos': renderProducts(contextId); break; } };
    const renderTiposProducto = () => { listingTitle.textContent = "Explora nuestras Familias de Productos"; listingGrid.innerHTML = MOCK_DATA.tiposProducto.map(tipo => `<div class="category-card" data-view="categorias" data-id="${tipo.id}"><div class="p-6"><h3 class="text-xl font-bold text-center mb-2">${tipo.nombre}</h3><p class="text-center text-gray-600">${tipo.descripcion}</p></div></div>`).join(''); showPage('categories-page'); };
    const renderCategorias = (tipoProductoId) => { const tipo = MOCK_DATA.tiposProducto.find(t => t.id === tipoProductoId); listingTitle.textContent = `Categorías de ${tipo.nombre}`; listingGrid.innerHTML = MOCK_DATA.categorias.filter(c => c.tipoProductoId === tipoProductoId).map(cat => `<div class="category-card" data-view="productos" data-id="${cat.id}"><img src="${cat.image}" alt="${cat.name}" class="w-full h-40 object-cover"><div class="p-4"><h3 class="text-xl font-bold text-center">${cat.name}</h3></div></div>`).join(''); showPage('categories-page'); };
    const renderProducts = (categoriaId) => { const cat = MOCK_DATA.categorias.find(c => c.id === categoriaId); productsTitle.textContent = cat.name; productsGrid.innerHTML = MOCK_DATA.productos.filter(p => p.categoriaId === categoriaId).map(prod => `<div class="product-card" data-product-id="${prod.id}"><img src="${prod.image}" alt="${prod.name}" class="w-full h-48 object-cover"><div class="p-3"><h4 class="font-bold text-center">${prod.name}</h4></div></div>`).join(''); showPage('products-page'); };
    const handleLogin = (e) => { e.preventDefault(); const phone = phoneInput.value.trim(); if (!phone) return; const storedUser = localStorage.getItem(`user_${phone}`); if (storedUser) { state.currentUser = JSON.parse(storedUser); navigateTo('tiposProducto'); } else { if (registrationFields.classList.contains('hidden')) { registrationFields.classList.remove('hidden'); nameInput.required = true; addressInput.required = true; alert('Eres nuevo. Completa tu nombre y dirección.'); return; } const name = nameInput.value.trim(); const address = addressInput.value.trim(); if (!name || !address) return; state.currentUser = { phone, name, address }; localStorage.setItem(`user_${phone}`, JSON.stringify(state.currentUser)); navigateTo('tiposProducto'); } };
    const changeQuantity = (variationId, change) => { const item = state.cart.items.find(i => i.variationId === variationId); if (item) { item.quantity += change; if (item.quantity <= 0) { state.cart.items = state.cart.items.filter(i => i.variationId !== variationId); } } localStorage.setItem('cart', JSON.stringify(state.cart)); renderCart(); };
    const clearCart = () => { if(confirm('¿Vaciar el carrito?')) { state.cart = { items: [], appliedPromoCode: null }; localStorage.removeItem('cart'); renderCart(); } };
    const toggleCart = (forceOpen = null) => { const isOpen = !cartSidebar.classList.contains('translate-x-full'); if (forceOpen === true || (forceOpen === null && !isOpen)) { cartSidebar.classList.remove('translate-x-full'); } else { cartSidebar.classList.add('translate-x-full'); closeModal(); } };
    const closeModal = () => { modalOverlay.classList.add('hidden'); productModal.classList.add('translate-y-full'); };
    const showConfirmationToast = () => { confirmationToast.classList.remove('opacity-0', 'translate-y-10'); setTimeout(() => { confirmationToast.classList.add('opacity-0', 'translate-y-10'); }, 2000); };

    loginForm.addEventListener('submit', handleLogin);
    backToCategoriesBtn.addEventListener('click', navigateBack);
    listingGrid.addEventListener('click', (e) => { const card = e.target.closest('.category-card'); if (card) navigateTo(card.dataset.view, Number(card.dataset.id)); });
    productsGrid.addEventListener('click', (e) => { const card = e.target.closest('.product-card'); if (card) openProductModal(Number(card.dataset.productId)); });
    modalOverlay.addEventListener('click', closeModal);
    modalQuantityPlus.addEventListener('click', () => { state.modalSelection.quantity++; updateModalUI(); });
    modalQuantityMinus.addEventListener('click', () => { if (state.modalSelection.quantity > 1) { state.modalSelection.quantity--; updateModalUI(); } });
    modalProductAttributesContainer.addEventListener('click', (e) => { const option = e.target.closest('.variation-option, .color-swatch'); if (option) { const defId = option.dataset.atributoDefId; const valId = Number(option.dataset.valorId); option.parentElement.querySelectorAll('.selected').forEach(el => el.classList.remove('selected')); option.classList.add('selected'); state.modalSelection.selectedAtributos[defId] = valId; updateModalUI(); } });
    modalAddToCartBtn.addEventListener('click', addToCart);
    cartToggleBtn.addEventListener('click', () => toggleCart());
    closeCartBtn.addEventListener('click', () => toggleCart(false));
    clearCartBtn.addEventListener('click', clearCart);
    checkoutBtn.addEventListener('click', handleCheckout);
    cartItemsContainer.addEventListener('click', e => { if (e.target.classList.contains('quantity-change')) { changeQuantity(Number(e.target.closest('[data-variation-id]').dataset.variationId), Number(e.target.dataset.change)); } });
    cartFooter.addEventListener('click', e => { if (e.target.id === 'apply-promo-btn') applyPromo(); if (e.target.id === 'remove-promo-btn') removePromo(); });

    const init = () => {
        const totalContainer = document.getElementById('cart-total')?.parentElement;
        if(totalContainer) totalContainer.id = 'cart-totals-summary';
        const promoContainer = document.createElement('div');
        promoContainer.id = 'cart-promo-section';
        promoContainer.className = 'my-4';
        cartFooter.insertBefore(promoContainer, checkoutBtn);
        const savedCart = localStorage.getItem('cart');
        if (savedCart) {
            const parsedCart = JSON.parse(savedCart);
            state.cart.items = parsedCart.items || [];
            state.cart.appliedPromoCode = parsedCart.appliedPromoCode || null;
        }
        showPage('login-page');
        renderCart();
    };
    init();
});
