// Funciones de utilidad
function formatMoney(value) {
    if (!value && value !== 0) return '';
    const number = parseFloat(value.toString().replace(/[^\d]/g, '')) || 0;
    return number.toLocaleString('es-CL', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}

function cleanMoney(value) {
    if (!value) return '';
    return value.toString().replace(/[^\d]/g, '');
}

// Funciones para documentos
function seleccionarCotizacion(numeroCotizacion) {
    document.getElementById('numero_cotizacion').value = numeroCotizacion;
}

// Funciones de búsqueda
function buscarCotizacionesRelacionadas() {
    const cliente = document.getElementById('cliente').value.trim();
    const montoTotal = cleanMoney(document.getElementById('monto_total').value);
    
    if (!cliente && !montoTotal) return;

    fetch(`/buscar_cotizaciones?cliente=${encodeURIComponent(cliente)}&monto=${encodeURIComponent(montoTotal)}`)
        .then(response => response.json())
        .then(cotizaciones => {
            const tbody = document.getElementById('cotizacionesRelacionadas');
            tbody.innerHTML = '';

            if (cotizaciones.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">No se encontraron cotizaciones relacionadas</td></tr>';
                return;
            }

            cotizaciones.forEach(cot => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${cot.numero}</td>
                    <td>${cot.empresa}</td>
                    <td>${new Date(cot.fecha).toLocaleDateString()}</td>
                    <td>$${formatMoney(cot.monto_total)}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="seleccionarCotizacion('${cot.numero}')">
                            Seleccionar
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error('Error:', error));
}

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    // Manejo del checkbox de facturado
    const facturadoCheckbox = document.getElementById('facturado');
    if (facturadoCheckbox) {
        facturadoCheckbox.addEventListener('change', function() {
            document.getElementById('numero_factura').disabled = !this.checked;
        });
    }

    // Manejo del formato de montos
    const montoInput = document.getElementById('monto_total');
    if (montoInput) {
        // Formatear al cargar
        if (montoInput.value) {
            montoInput.value = formatMoney(montoInput.value);
        }

        // Manejar entrada de números
        montoInput.addEventListener('input', function(e) {
            const cursorPosition = this.selectionStart;
            const oldLength = this.value.length;
            
            const cleanValue = cleanMoney(this.value);
            const formattedValue = formatMoney(cleanValue);
            this.value = formattedValue;
            
            const newLength = this.value.length;
            const newPosition = cursorPosition + (newLength - oldLength);
            this.setSelectionRange(newPosition, newPosition);
        });
    }

    // Manejo del formulario
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const montoInput = document.getElementById('monto_total');
            montoInput.value = cleanMoney(montoInput.value);
            this.submit();
        });
    }

    // Eventos para búsqueda de cotizaciones
    let searchTimeout;
    ['cliente', 'monto_total'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(buscarCotizacionesRelacionadas, 500);
            });
        }
    });

    // Autocompletado de clientes
    const clienteInput = document.getElementById('cliente');
    const sugerenciasDiv = document.getElementById('clientesSugerencias');
    let timeoutId = null;

    if (clienteInput && sugerenciasDiv) {
        clienteInput.addEventListener('input', function() {
            clearTimeout(timeoutId);
            const query = this.value.trim();
            
            if (query.length < 2) {
                sugerenciasDiv.classList.add('d-none');
                return;
            }

            timeoutId = setTimeout(() => {
                fetch(`/clientes/buscar_cliente?empresa=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(clientes => {
                        sugerenciasDiv.innerHTML = '';
                        const clientesFiltrados = clientes
                            .filter(cliente => cliente.empresa && cliente.empresa.toLowerCase().includes(query.toLowerCase()))
                            .sort((a, b) => {
                                const empresaA = a.empresa.toLowerCase();
                                const empresaB = b.empresa.toLowerCase();
                                const queryLower = query.toLowerCase();
                                
                                const startWithA = empresaA.startsWith(queryLower);
                                const startWithB = empresaB.startsWith(queryLower);
                                
                                if (startWithA && !startWithB) return -1;
                                if (!startWithA && startWithB) return 1;
                                
                                return empresaA.localeCompare(empresaB);
                            });

                        if (clientesFiltrados.length > 0) {
                            clientesFiltrados.forEach(cliente => {
                                const item = document.createElement('a');
                                item.href = '#';
                                item.className = 'list-group-item list-group-item-action';
                                item.innerHTML = `
                                    <div class="d-flex justify-content-between align-items-center">
                                        <strong>${cliente.empresa || ''}</strong>
                                        <small>${cliente.rut || ''}</small>
                                    </div>
                                    <small class="text-muted">${cliente.nombre || ''}</small>
                                `;
                                item.addEventListener('click', (e) => {
                                    e.preventDefault();
                                    clienteInput.value = cliente.empresa || '';
                                    document.getElementById('contacto').value = cliente.nombre || '';
                                    sugerenciasDiv.classList.add('d-none');
                                    buscarCotizacionesRelacionadas();
                                });
                                sugerenciasDiv.appendChild(item);
                            });
                            sugerenciasDiv.classList.remove('d-none');
                        } else {
                            sugerenciasDiv.innerHTML = '<div class="list-group-item">No se encontraron empresas</div>';
                            sugerenciasDiv.classList.remove('d-none');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        sugerenciasDiv.classList.add('d-none');
                    });
            }, 300);
        });

        // Ocultar sugerencias al hacer clic fuera
        document.addEventListener('click', function(e) {
            if (!clienteInput.contains(e.target) && !sugerenciasDiv.contains(e.target)) {
                sugerenciasDiv.classList.add('d-none');
            }
        });
    }
});
