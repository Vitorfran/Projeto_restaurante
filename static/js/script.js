let cart = [];
const mesaId = window.mesaId || null;

// Funções do carrinho
function addToCart(item, price, tamanho = null, sabores = [], event = null) {
  const cartItem = {
    item: item,
    price: parseFloat(price),
    tamanho: tamanho,
    sabores: sabores
  };
  
  cart.push(cartItem);
  updateCart();
  
  if (event?.target) {
    const btn = event.target;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Adicionado';
    btn.classList.replace('btn-primary', 'btn-success');
    btn.disabled = true;
    
    setTimeout(() => {
      btn.innerHTML = originalHTML;
      btn.classList.replace('btn-success', 'btn-primary');
      btn.disabled = false;
    }, 2000);
  }
}

// Função para enviar pedido
async function enviarPedido() {
  if (cart.length === 0) {
    alert('Por favor, adicione itens ao carrinho');
    return;
  }

  const isRetirada = document.getElementById('retiradaCheckbox').checked;
  const pagamento = document.querySelector('input[name="paymentMethod"]:checked')?.value || 'Não informado';
  const troco = pagamento === 'Dinheiro' ? document.getElementById('trocoPara').value.trim() : '';

  const pedidoData = {
    mesa_id: mesaId || null,
    items: cart,
    nome_cliente: document.getElementById('customerName').value.trim(),
    telefone: isRetirada ? null : document.getElementById('customerPhone').value.trim(),
    endereco: isRetirada ? null : document.getElementById('customerAddress').value.trim(),
    complemento: isRetirada ? null : document.getElementById('customerComplement')?.value.trim() || '',
    observacoes: document.getElementById('customerObservations')?.value.trim() || '',
    forma_pagamento: pagamento,
    troco_para: troco || null,
    retirada: isRetirada
  };

  try {
    const response = await fetch('/fazer_pedido', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(pedidoData)
    });

    const data = await response.json();
    
    if (data.status === 'success') {
      alert(`Pedido #${data.pedido_id} enviado com sucesso!`);
      cart = [];
      updateCart();
    } else {
      alert('Erro: ' + (data.message || 'Falha no envio'));
    }
  } catch (error) {
    alert('Erro ao enviar pedido: ' + error.message);
  }
}





// Demais funções do carrinho (updateCart, removeItem, clearCart, etc.)
// ...