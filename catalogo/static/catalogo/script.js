// catalogo/script.js

document.addEventListener('DOMContentLoaded', () => {
    const DATA = window.INITIAL_DATA;
    const WHATSAPP_NUMBER = window.WHATSAPP_NUMBER;

    let state = {
        currentUser: null,
        cart: { items: [], appliedPromoCode: null },
        navigationStack: [],
        modalSelection: { productoId: null, variation: null, quantity: 1, selectedAtributos: {} }
    };

    // --- Selectores de Elementos ---
    const pages = document.querySelectorAll('.page');
    const loginForm = document.getElementById('login-form');
    const phoneInput = document.getElementById('phone');
    const cityInput = document.getElementById('city');
    const registrationFields = document.getElementById('registration-fields');
    const nameInput = document.getElementById('name');
    const addressInput = document.getElementById('address');
    const listingPage = document.getElementById('categories-page');
    const listingGrid = document.getElementById('categories-grid');
    const listingTitle = listingPage.querySelector('h2');
    const breadcrumb = document.getElementById('breadcrumb');
    const productsPage = document.getElementById('products-page');
    const productsGrid = document.getElementById('products-grid');
    const productsTitle = document.getElementById('products-title');
    const backToCategoriesBtn = document.getElementById('back-to-categories');
    const backToTypesBtn = document.getElementById('back-to-types');
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


    function getCookie(name) {
        const v = document.cookie.split("; ").find(c => c.startsWith(name + "="));
        return v ? decodeURIComponent(v.split("=")[1]) : null;
    }

    async function syncCartWithServer() {
        if (!state.currentUser) return;
        try {
            await fetch('/catalogo/api/cart/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({
                    phone: state.currentUser.phone,
                    items: state.cart.items.map(item => ({
                        variationId: item.variationId,
                        quantity: item.quantity
                    }))
                })
            });
        } catch (error) {
            console.error('Failed to sync cart with server:', error);
        }
    }
    
    const openProductModal = (productoId) => {
        const producto = DATA.productos.find(p => p.id === productoId);
        if (!producto) return;
        state.modalSelection = { productoId, variation: null, quantity: 1, selectedAtributos: {} };
        modalProductImg.src = producto.foto_url;
        modalProductName.textContent = producto.referencia;
        const dynamicContent = modalProductAttributesContainer.querySelector('#dynamic-attributes');
        if (dynamicContent) dynamicContent.remove();
        const variaciones = DATA.variacionesProducto.filter(v => v.productoId === productoId);
        if (variaciones.length === 0) return;
        const allValorAtributoIds = [...new Set(variaciones.flatMap(v => v.valorAtributoIds))];
        const allAtributoDefIds = [...new Set(allValorAtributoIds.map(valId => DATA.valorAtributos.find(v => v.id === valId).atributoDefId))];
        let attributesHTML = '<div id="dynamic-attributes" class="space-y-6">';
        allAtributoDefIds.forEach(defId => {
            const atributoDef = DATA.atributoDefs.find(def => def.id === defId);
            const valoresDisponibles = [...new Set(variaciones.flatMap(v => v.valorAtributoIds))]
                .map(valId => DATA.valorAtributos.find(v => v.id === valId))
                .filter(val => val.atributoDefId === defId);
            let optionsHTML = valoresDisponibles.map(val => {
                if (atributoDef.nombre.toLowerCase() === 'color') {
                    return `<button type="button" class="variation-option color-option" data-atributo-def-id="${defId}" data-valor-id="${val.id}" style="--option-color:${val.display || '#ccc'}">${val.valor}</button>`;
                }
                return `<button type="button" class="variation-option" data-atributo-def-id="${defId}" data-valor-id="${val.id}">${val.valor}</button>`;
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
        const variacionesDisponibles = DATA.variacionesProducto.filter(v => v.productoId === productoId);
        const allOptions = modalProductAttributesContainer.querySelectorAll('[data-valor-id]');
        allOptions.forEach(opt => {
            const defId = Number(opt.dataset.atributoDefId);
            const valId = Number(opt.dataset.valorId);
            const match = variacionesDisponibles.some(v => {
                if (!v.valorAtributoIds.includes(valId)) return false;
                return Object.entries(selectedAtributos).every(([d, vId]) => {
                    if (Number(d) === defId) return true;
                    return v.valorAtributoIds.includes(vId);
                });
            });
            opt.classList.toggle('opacity-30', !match);
            opt.classList.toggle('pointer-events-none', !match);
        });
        const totalAtributosRequeridos = [...new Set(variacionesDisponibles.flatMap(v => v.valorAtributoIds).map(valId => DATA.valorAtributos.find(v => v.id === valId).atributoDefId))].length;
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
            const producto = DATA.productos.find(p => p.id === variation.productoId);
            const atributos = variation.valorAtributoIds.map(valId => {
                const valor = DATA.valorAtributos.find(v => v.id === valId);
                const definicion = DATA.atributoDefs.find(d => d.id === valor.atributoDefId);
                return { nombre: definicion.nombre, valor: valor.valor };
            });
            state.cart.items.push({
                variationId: variation.id,
                productoId: producto.id,
                name: producto.referencia,
                image: producto.foto_url,
                priceBase: variation.precioBase,
                quantity,
                atributos,
            });
        }
        renderCart();
        syncCartWithServer();
        closeModal();
        showConfirmationToast();
    };


const renderCart = () => {

        const { items } = state.cart;
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
                        <button class="remove-item text-red-600 font-bold p-2">x</button>
                    </div>
                </div>`;
            }).join('');
            checkoutBtn.disabled = false;
        }
        const subtotal = items.reduce((sum, item) => sum + item.priceBase * item.quantity, 0);

        let discount = 0;
        let promo = null;
        /* Promo code feature disabled for now
        if (appliedPromoCode) {
            promo = DATA.promos.find(p => p.codigo === appliedPromoCode);
            if (promo) discount = subtotal * (promo.porcentaje / 100);
        }
        */
        const total = subtotal - discount;

        const totalsElement = cartFooter.querySelector('#cart-totals-summary');
        totalsElement.innerHTML = `
            <div class="flex justify-between items-center text-lg">
                <span>Subtotal:</span>
                <span class="font-semibold">$${subtotal.toLocaleString('es-CO')}</span>
            </div>
            <div class="flex justify-between items-center mt-2 pt-2 border-t">
                <span class="text-xl font-bold">Total:</span>
                <span class="text-2xl font-extrabold text-gray-900">$${total.toLocaleString('es-CO')}</span>
            </div>`;
        const promoElement = cartFooter.querySelector('#cart-promo-section');

        /* Promo code UI disabled
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
        */
        if (promoElement) promoElement.innerHTML = '';
        localStorage.setItem('cart', JSON.stringify(state.cart));
    };

    /*
    const applyPromo = () => {
        const input = document.getElementById('promo-code-input');
        const errorP = document.getElementById('promo-error');
        const code = input.value.trim().toUpperCase();
        if (!code) return;
        const promo = DATA.promos.find(p => p.codigo === code);
        const now = new Date();
        if (promo && promo.activo && new Date(promo.fecha_inicio) <= now && new Date(promo.fecha_fin) >= now) {
            state.cart.appliedPromoCode = code;
            renderCart();
        } else {
            errorP.textContent = "Código inválido o expirado.";
            input.value = '';
        }
    };

    const removePromo = () => {
        state.cart.appliedPromoCode = null;
        renderCart();
    };
    */

    

    const handleCheckout = async () => {
        if (!state.currentUser) { alert("Por favor, inicia sesión para continuar."); toggleCart(false); showPage('login-page'); return; }
        let message = `¡Hola! 👋 Quisiera hacer el siguiente pedido:\n\n`;
        const { items } = state.cart;
        items.forEach(item => {
            const atributosDesc = item.atributos.map(a => `${a.nombre}: ${a.valor}`).join('\n  - ');
            message += `*Producto:* ${item.name}\n  - ${atributosDesc}\n  - Cantidad: ${item.quantity}\n  - Precio Base: $${(item.priceBase * item.quantity).toLocaleString('es-CO')}\n\n`;
        });
        const subtotal = items.reduce((sum, item) => sum + item.priceBase * item.quantity, 0);

        let discount = 0;
        let promo = null;
        /* Promo code feature disabled for now
        if (appliedPromoCode) {
            promo = DATA.promos.find(p => p.codigo === appliedPromoCode);
            if (promo) discount = subtotal * (promo.porcentaje / 100);
        }
        */
        const total = subtotal - discount;
        message += `*Subtotal:* $${subtotal.toLocaleString('es-CO')}\n`;
        /* if (promo) {
            message += `*Descuento (${promo.porcentaje}%):* -$${discount.toLocaleString('es-CO')}\n`;
        }*/

        message += `*TOTAL DEL PEDIDO: $${total.toLocaleString('es-CO')}*\n\n`;
        message += `*Datos de Envío:*\n- Nombre: ${state.currentUser.name}\n- Dirección: ${state.currentUser.address}\n- Ciudad: ${state.currentUser.city}\n- Teléfono: ${state.currentUser.phone}\n\n¡Gracias!`;
        const response = await fetch('/catalogo/api/pedido/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({

                cliente: state.currentUser,
                // promoCode: appliedPromoCode

            })
        });
        if (!response.ok) {
            const errorData = await response.text();
            alert(`Error guardando el pedido: ${errorData}. Inténtalo de nuevo.`);
            return;
        }
        const whatsappUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;
        window.open(whatsappUrl, '_blank');
        state.cart = { items: [], appliedPromoCode: null };
        renderCart();
        toggleCart(false);
        alert('¡Gracias! Serás redirigido a WhatsApp para confirmar tu pedido.');
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        const phone = phoneInput.value.trim();
        if (!phone) return;
        const proceedToCatalog = async (userData) => {
            state.currentUser = userData;
            localStorage.setItem('currentUser', JSON.stringify(state.currentUser));
            try {
                const cartRes = await fetch(`/catalogo/api/cart/?phone=${state.currentUser.phone}`);
                if (cartRes.ok) {
                    state.cart = await cartRes.json();
                } else {
                    state.cart = { items: [], appliedPromoCode: null };
                }
            } catch (error) {
                console.error("Error fetching cart:", error);
                state.cart = { items: [], appliedPromoCode: null };
            }
            renderCart();
            restoreNavigationFromUrl();
            renderCurrentView();
            updateHistory(true);
        };
        if (registrationFields.classList.contains("hidden")) {
            const res = await fetch(`/catalogo/api/cliente/detail/?phone=${phone}`);
            if (res.ok) {
                const userData = await res.json();
                await proceedToCatalog(userData);
            } else if (res.status === 404) {
                registrationFields.classList.remove("hidden");
                nameInput.required = true;
                addressInput.required = true;
                cityInput.required = true;
                alert("Parece que eres nuevo/a. Por favor, completa tus datos para registrarte.");
            } else {
                alert("Ocurrió un error. Inténtalo de nuevo.");
            }
        } else {
            const payload = { phone, name: nameInput.value.trim(), address: addressInput.value.trim(), city: cityInput.value.trim() };
            if(!payload.name || !payload.address || !payload.city) {
                alert("Por favor, completa todos los campos.");
                return;
            }
            const res = await fetch("/catalogo/api/cliente/", {method: "POST", headers: {"Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken")}, body: JSON.stringify(payload)});
            if (res.ok) {
                const userData = await res.json();
                await proceedToCatalog(userData);
            } else {
                alert("No se pudo completar el registro. Inténtalo de nuevo.");
            }
        }
    };

    const changeQuantity = (variationId, change) => {
        const item = state.cart.items.find(i => i.variationId === variationId);
        if (item) {
            item.quantity += change;
            if (item.quantity <= 0) {
                state.cart.items = state.cart.items.filter(i => i.variationId !== variationId);
            }
        }
        renderCart();
        syncCartWithServer();
    };
    
    const clearCart = () => { 
        if(confirm('¿Estás seguro de que quieres vaciar el carrito?')) { 
            state.cart = { items: [], appliedPromoCode: null };
            renderCart();
            syncCartWithServer();
        }
    };
    
    const toggleCart = (forceOpen = null) => {
        const isOpen = !cartSidebar.classList.contains('translate-x-full');
        if (forceOpen === true || (forceOpen === null && !isOpen)) {
            cartSidebar.classList.remove('translate-x-full');
        } else {
            cartSidebar.classList.add('translate-x-full');
            closeModal();
        }
    };

    const closeModal = () => {
        modalOverlay.classList.add('hidden');
        productModal.classList.add('translate-y-full');
    };

    const showConfirmationToast = () => {
        confirmationToast.classList.remove('opacity-0', 'translate-y-10');
        setTimeout(() => {
            confirmationToast.classList.add('opacity-0', 'translate-y-10');
        }, 2000);
    };

    // --- LÓGICA DE NAVEGACIÓN ---

    const showPage = (pageId) => {
        pages.forEach(page => page.classList.add('hidden'));
        document.getElementById(pageId).classList.remove('hidden');
        window.scrollTo(0, 0);
    };

    const updateHistory = (replace = false) => {
        if (state.navigationStack.length === 0) return;
        const { view, contextId } = state.navigationStack[state.navigationStack.length - 1];
        const params = new URLSearchParams();
        if (view === 'categorias') {
            params.set('view', 'categorias');
            params.set('tipo', contextId);
        } else if (view === 'productos') {
            params.set('view', 'productos');
            params.set('cat', contextId);
        }
        const url = params.toString() ? `?${params.toString()}` : location.pathname;
        if (replace) history.replaceState(null, '', url); else history.pushState(null, '', url);
    };

    const restoreNavigationFromUrl = () => {
        const params = new URLSearchParams(location.search);
        const view = params.get('view');
        state.navigationStack = [];
        if (view === 'productos' && params.get('cat')) {
            const catId = Number(params.get('cat'));
            const cat = DATA.categorias.find(c => c.id === catId);
            if (cat) {
                state.navigationStack.push({ view: 'tiposProducto', contextId: null });
                state.navigationStack.push({ view: 'categorias', contextId: cat.tipoProductoId });
                state.navigationStack.push({ view: 'productos', contextId: catId });
                return;
            }
        }
        if (view === 'categorias' && params.get('tipo')) {
            const tipoId = Number(params.get('tipo'));
            state.navigationStack.push({ view: 'tiposProducto', contextId: null });
            state.navigationStack.push({ view: 'categorias', contextId: tipoId });
            return;
        }
        state.navigationStack.push({ view: 'tiposProducto', contextId: null });
    };

    const navigateTo = (view, contextId = null) => {
        state.navigationStack.push({ view, contextId });
        updateHistory();
        renderCurrentView();
    };

    const navigateBack = () => {
        if (state.navigationStack.length > 1) {
            state.navigationStack.pop();
            updateHistory();
            renderCurrentView();
        }
    };
    
    const navigateToView = (index) => {
        if (index < 0 || index >= state.navigationStack.length) return;
        state.navigationStack = state.navigationStack.slice(0, index + 1);
        updateHistory();
        renderCurrentView();
    };

    const updateBreadcrumb = () => {
        if (state.navigationStack.length <= 1) {
            breadcrumb.innerHTML = '';
            breadcrumb.classList.add('hidden');
            return;
        }
        const breadcrumbParts = state.navigationStack.map(({ view, contextId }, index) => {
            let name = '';
            const isLast = index === state.navigationStack.length - 1;
            if (view === 'tiposProducto') name = 'Tipos de Producto';
            else if (view === 'categorias') {
                const tipo = DATA.tiposProducto.find(t => t.id === contextId);
                name = tipo ? tipo.nombre : 'Categorías';
            } else if (view === 'productos') {
                const cat = DATA.categorias.find(c => c.id === contextId);
                name = cat ? cat.nombre : 'Productos';
            }
            if (isLast) {
                return `<span class="font-bold text-gray-500">${name}</span>`;
            } else {
                return `<a href="#" class="text-blue-600 hover:underline" data-nav-index="${index}">${name}</a>`;
            }
        });
        breadcrumb.innerHTML = breadcrumbParts.join('<span class="mx-2 text-gray-400">/</span>');
        breadcrumb.classList.remove('hidden');
    };

    const renderCurrentView = () => {
        if (state.navigationStack.length === 0) return;
        const { view, contextId } = state.navigationStack[state.navigationStack.length - 1];
        backToCategoriesBtn.style.display = 'none';
        backToTypesBtn.style.display = 'none';
        switch (view) {
            case 'tiposProducto':
                renderTiposProducto();
                break;
            case 'categorias':
                renderCategorias(contextId);
                backToTypesBtn.style.display = 'block';
                break;
            case 'productos':
                renderProducts(contextId);
                backToCategoriesBtn.style.display = 'block';
                break;
        }
        updateBreadcrumb();
    };
    
    const renderTiposProducto = () => {
        listingTitle.textContent = "Explora nuestras Familias de Productos";
        listingGrid.innerHTML = DATA.tiposProducto.map(tipo => `
            <div class="category-card cursor-pointer" data-view="categorias" data-id="${tipo.id}">
                ${tipo.imagen_url ? `<img src="${tipo.imagen_url}" alt="${tipo.nombre}" class="w-full h-40 object-cover">` : ''}
                <div class="p-6">
                    <h3 class="text-xl font-bold text-center mb-2">${tipo.nombre}</h3>
                    <p class="text-center text-gray-600">${tipo.descripcion}</p>
                </div>
            </div>
        `).join('');
        showPage('categories-page');
    };

    const renderCategorias = (tipoProductoId) => {
        const tipo = DATA.tiposProducto.find(t => t.id === tipoProductoId);
        listingTitle.textContent = `Categorías de ${tipo ? tipo.nombre : ''}`;
        listingGrid.innerHTML = DATA.categorias
            .filter(c => c.tipoProductoId === tipoProductoId)
            .map(cat => `<div class="category-card cursor-pointer" data-view="productos" data-id="${cat.id}"><img src="${cat.imagen_url}" alt="${cat.nombre}" class="w-full h-40 object-cover"><div class="p-4"><h3 class="text-xl font-bold text-center">${cat.nombre}</h3></div></div>`)
            .join('');
        showPage('categories-page');
    };

    const renderProducts = (categoriaId) => {
        const cat = DATA.categorias.find(c => c.id === categoriaId);
        productsTitle.textContent = cat ? cat.nombre : '';
        productsGrid.innerHTML = DATA.productos
            // --- LÍNEA MODIFICADA ---
            // Cambiamos p.categoriaId === categoriaId por p.categoriaIds.includes(categoriaId)
            .filter(p => p.categoriaIds.includes(categoriaId))
            .map(prod => `<div class="product-card cursor-pointer" data-product-id="${prod.id}"><img src="${prod.foto_url}" alt="${prod.referencia}" class="w-full h-48 object-contain p-2 bg-white"><div class="p-3"><h4 class="font-bold text-center">${prod.referencia}</h4></div></div>`)
            .join('');
        showPage('products-page');
    };

    // --- EVENT LISTENERS ---
    loginForm.addEventListener('submit', handleLogin);
    backToCategoriesBtn.addEventListener('click', navigateBack);
    backToTypesBtn.addEventListener('click', navigateBack);
    listingGrid.addEventListener('click', (e) => {
        const card = e.target.closest('.category-card');
        if (card) navigateTo(card.dataset.view, Number(card.dataset.id));
    });
    productsGrid.addEventListener('click', (e) => {
        const card = e.target.closest('.product-card');
        if (card) openProductModal(Number(card.dataset.productId));
    });
    breadcrumb.addEventListener('click', (e) => {
        e.preventDefault();
        const target = e.target.closest('a[data-nav-index]');
        if (target) {
            const index = parseInt(target.dataset.navIndex, 10);
            navigateToView(index);
        }
    });
    window.addEventListener('popstate', () => { restoreNavigationFromUrl(); renderCurrentView(); });
    modalOverlay.addEventListener('click', closeModal);
    modalQuantityPlus.addEventListener('click', () => { state.modalSelection.quantity++; updateModalUI(); });
    modalQuantityMinus.addEventListener('click', () => { if (state.modalSelection.quantity > 1) { state.modalSelection.quantity--; updateModalUI(); } });
    modalProductAttributesContainer.addEventListener('click', (e) => {

        const option = e.target.closest('.variation-option, .color-option');

        if (option) {
            const defId = option.dataset.atributoDefId;
            const valId = Number(option.dataset.valorId);
            const parent = option.parentElement;
            if (parent.querySelector('.selected')) {
                parent.querySelector('.selected').classList.remove('selected');
            }
            option.classList.add('selected');
            state.modalSelection.selectedAtributos[defId] = valId;
            updateModalUI();
        }
    });
    modalAddToCartBtn.addEventListener('click', addToCart);
    cartToggleBtn.addEventListener('click', () => toggleCart());
    closeCartBtn.addEventListener('click', () => toggleCart(false));
    clearCartBtn.addEventListener('click', clearCart);
    checkoutBtn.addEventListener('click', handleCheckout);
    cartItemsContainer.addEventListener('click', e => {
        if (e.target.classList.contains('quantity-change')) {
            changeQuantity(Number(e.target.closest('[data-variation-id]').dataset.variationId), Number(e.target.dataset.change));
        }
        if (e.target.classList.contains('remove-item')) {
            changeQuantity(Number(e.target.closest('[data-variation-id]').dataset.variationId), -Infinity);
        }
    });

    /* Promo code actions disabled
    cartFooter.addEventListener('click', e => {
        if (e.target.id === 'apply-promo-btn') applyPromo();
        if (e.target.id === 'remove-promo-btn') removePromo();
    });
    */


    const init = () => {
        const totalContainer = document.getElementById('cart-total')?.parentElement;
        if(totalContainer) totalContainer.id = 'cart-totals-summary';

        /* Promo code UI container disabled
        const promoContainer = document.createElement('div');
        promoContainer.id = 'cart-promo-section';
        promoContainer.className = 'my-4';
        cartFooter.insertBefore(promoContainer, checkoutBtn);
        */

        const storedUser = localStorage.getItem('currentUser');
        const storedCart = localStorage.getItem('cart');
        if (storedUser) {
            try {
                state.currentUser = JSON.parse(storedUser);
            } catch (e) { state.currentUser = null; }
        }
        if (storedCart) {
            try {
                state.cart = JSON.parse(storedCart);
            } catch (e) { state.cart = { items: [], appliedPromoCode: null }; }
        }
        if (state.currentUser) {
            fetch(`/catalogo/api/cart/?phone=${state.currentUser.phone}`)
                .then(res => res.ok ? res.json() : Promise.reject())
                .then(data => { state.cart = data; renderCart(); })
                .catch(() => { renderCart(); });
            restoreNavigationFromUrl();
            renderCurrentView();
            updateHistory(true);
        } else {
            showPage('login-page');
            renderCart();
        }
        updateBreadcrumb();
    };

    init();
});