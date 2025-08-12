// Función para ordenar tabla por fecha
function sortTableByDate() {
    console.log('Función sortTableByDate llamada');
    
    const table = document.querySelector('table');
    console.log('Tabla encontrada:', table);
    
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    console.log('Filas encontradas:', rows.length);
    
    const dateColumn = 1; // La columna de fecha es la segunda (índice 1)
    const isAscending = table.getAttribute('data-sort') !== 'desc';  // Cambiado la lógica
    console.log('Orden actual:', isAscending ? 'ascendente' : 'descendente');

    // Actualizar el atributo de ordenamiento
    table.setAttribute('data-sort', isAscending ? 'desc' : 'asc');

    // Actualizar el ícono
    const dateHeader = document.getElementById('dateHeader');
    console.log('Header de fecha encontrado:', dateHeader);
    const icon = dateHeader.querySelector('i');
    console.log('Ícono encontrado:', icon);
    icon.className = `bi bi-sort-${isAscending ? 'down' : 'up'}`;

    rows.sort((rowA, rowB) => {
        const dateTextA = rowA.cells[dateColumn].textContent.trim();
        const dateTextB = rowB.cells[dateColumn].textContent.trim();
        console.log('Comparando fechas:', dateTextA, dateTextB);
        
        // Convertir fecha de formato DD-MM-YYYY a objeto Date
        const [dayA, monthA, yearA] = dateTextA.split('-');
        const [dayB, monthB, yearB] = dateTextB.split('-');
        
        const dateA = new Date(yearA, monthA - 1, dayA);
        const dateB = new Date(yearB, monthB - 1, dayB);
        
        console.log('Fechas convertidas:', dateA, dateB);
        
        return isAscending ? dateA - dateB : dateB - dateA;
    });

    // Limpiar y reinsertarar las filas ordenadas
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// Funciones de utilidad
function formatMoney(value) {
    if (!value && value !== 0) return '';
    const number = parseFloat(value.toString().replace(/[^\d]/g, '')) || 0;
    return number.toLocaleString('es-CL');
}

function cleanMoney(value) {
    if (!value) return '';
    return value.toString()
        .replace(/\$/g, '')     // Eliminar símbolo de peso
        .replace(/\./g, '')      // Eliminar puntos
        .replace(/,/g, '.')      // Reemplazar coma por punto
        .replace(/[^\d.-]/g, '') // Solo permitir números, punto y signo menos
        .trim();
}

function validateNumberInput(value) {
    return value === '' || /^\d*$/.test(value);
}

// Funciones para selección de documentos
function seleccionarCotizacion(numeroCotizacion) {
    document.getElementById('numero_cotizacion').value = numeroCotizacion;
}

function seleccionarOrdenCompra(numeroOC) {
    document.getElementById('numero_oc').value = numeroOC;
}

// Funciones de búsqueda para cotizaciones Relacionadas
function buscarCotizacionesRelacionadas() {
    const montoTotal = cleanMoney($('#monto_total').val());
    
    if (!montoTotal) {
        $('#cotizacionesRelacionadas').html('<tr><td colspan="5" class="text-center">Ingrese el monto para buscar cotizaciones relacionadas</td></tr>');
        return;
    }

    const tbody = $('#cotizacionesRelacionadas');
    tbody.html('<tr><td colspan="5" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div></td></tr>');

    const params = new URLSearchParams({
        monto: montoTotal
    });

    fetch(`/buscar_cotizaciones?${params}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(cotizaciones => {
            tbody.empty();

            if (!cotizaciones || cotizaciones.length === 0) {
                tbody.html('<tr><td colspan="5" class="text-center">No se encontraron cotizaciones relacionadas</td></tr>');
                return;
            }

            cotizaciones.forEach(cot => {
                const row = $('<tr>');
                row.html(`
                    <td>${cot.numero || ''}</td>
                    <td>${cot.empresa || ''}</td>
                    <td>${cot.fecha ? new Date(cot.fecha).toLocaleDateString('es-CL') : ''}</td>
                    <td>$${formatMoney(cot.monto_total || 0)}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="seleccionarCotizacion('${cot.numero || ''}')">
                            Seleccionar
                        </button>
                    </td>
                `);
                tbody.append(row);
            });
        })
        .catch(error => {
            console.error('Error al buscar cotizaciones:', error);
            tbody.html('<tr><td colspan="5" class="text-center text-danger">Error al buscar cotizaciones</td></tr>');
        });
}


// Funciones de búsqueda para Ordenes Compra Relacionadas
function buscarOrdenesCompraRelacionadas() {
    const montoTotal = cleanMoney($('#monto_total').val());
    
    if (!montoTotal) {
        $('#ordenesCompraRelacionadas').html('<tr><td colspan="5" class="text-center">Ingrese el monto para buscar órdenes de compra relacionadas</td></tr>');
        return;
    }

    const tbody = $('#ordenesCompraRelacionadas');
    tbody.html('<tr><td colspan="5" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div></td></tr>');

    // Log para depuración
    console.log('Buscando órdenes de compra con monto:', montoTotal);

    const params = new URLSearchParams({
        monto: montoTotal
    });

    fetch(`/buscar_ordenes_compra?${params.toString()}`)
        .then(response => {
            if (!response.ok) {
                console.error('Error en la respuesta:', response.status, response.statusText);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(ordenes => {
            console.log('Órdenes recibidas:', ordenes); // Log para depuración
            tbody.empty();

            if (!ordenes || ordenes.length === 0) {
                tbody.html('<tr><td colspan="5" class="text-center">No se encontraron órdenes de compra relacionadas</td></tr>');
                return;
            }

            ordenes.forEach(oc => {
                // Asegurarse de que todos los campos existan
                const numeroOC = oc.numero_oc || oc.numero || '';
                const clienteNombre = oc.empresa || oc.cliente || '';
                const fecha = oc.fecha ? new Date(oc.fecha).toLocaleDateString('es-CL') : '';
                const monto = oc.monto_total || oc.monto || 0;
                const montoIngresado = parseInt(cleanMoney($('#monto_total').val()));
                const esMontoCorrecto = parseInt(monto) === montoIngresado;

                console.log('Procesando orden:', { numeroOC, clienteNombre, fecha, monto }); // Log para depuración

                const row = $('<tr>');
                row.html(`
                    <td>${numeroOC}</td>
                    <td>${clienteNombre}</td>
                    <td>${fecha}</td>
                    <td class="${esMontoCorrecto ? 'text-success fw-bold' : ''}">${formatMoney(monto)}
                        ${esMontoCorrecto ? '<i class="bi bi-check-circle-fill"></i>' : ''}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="seleccionarOrdenCompra('${numeroOC}')">
                            Seleccionar
                        </button>
                    </td>
                `);
                tbody.append(row);
            });
        })
        .catch(error => {
            console.error('Error al buscar órdenes de compra:', error);
            tbody.html('<tr><td colspan="5" class="text-center text-danger">Error al buscar órdenes de compra: ' + error.message + '</td></tr>');
        });
}

// Inicialización cuando el documento está listo
$(document).ready(function() {
    let typingTimer;
    const doneTypingInterval = 300;

    // Búsqueda de clientes con ordenamiento mejorado
    function buscarClientes() {
        const empresaBusqueda = $('#receptor').val().trim();
        if (!empresaBusqueda) {
            $('#clienteSuggestions').empty().hide();
            return;
        }
        
        fetch(`/clientes/buscar_cliente?empresa=${encodeURIComponent(empresaBusqueda)}`)
            .then(response => {
                if (!response.ok) throw new Error('Error en la búsqueda');
                return response.json();
            })
            .then(clientes => {
                const suggestions = $('#clienteSuggestions');
                suggestions.empty();
                
                // Filtrar y ordenar los clientes por coincidencia
                const clientesFiltrados = clientes
                    .filter(cliente => cliente.empresa && cliente.empresa.toLowerCase().includes(empresaBusqueda.toLowerCase()))
                    .sort((a, b) => {
                        const empresaA = a.empresa.toLowerCase();
                        const empresaB = b.empresa.toLowerCase();
                        const queryLower = empresaBusqueda.toLowerCase();
                        
                        // Priorizar coincidencias exactas al inicio
                        const startWithA = empresaA.startsWith(queryLower);
                        const startWithB = empresaB.startsWith(queryLower);
                        
                        if (startWithA && !startWithB) return -1;
                        if (!startWithA && startWithB) return 1;
                        
                        return empresaA.localeCompare(empresaB);
                    });
                
                if (clientesFiltrados.length > 0) {
                    clientesFiltrados.forEach(cliente => {
                        const div = $('<div>')
                            .addClass('cliente-suggestion')
                            .html(`
                                <div class="d-flex justify-content-between align-items-center">
                                    <strong>${cliente.empresa || ''}</strong>
                                    <small>${cliente.rut || ''}</small>
                                </div>
                                <small class="text-muted">${cliente.nombre || ''}</small>
                            `)
                            .data('cliente', cliente)
                            .click(function() {
                                const clienteData = $(this).data('cliente');
                                $('#receptor').val(clienteData.empresa);
                                $('#rut_receptor').val(clienteData.rut);
                                suggestions.hide();
                                buscarCotizacionesRelacionadas();
                                buscarOrdenesCompraRelacionadas();
                            });
                        suggestions.append(div);
                    });
                    suggestions.show();
                } else {
                    suggestions.html('<div class="cliente-suggestion text-muted">No se encontraron empresas</div>').show();
                }
            })
            .catch(error => {
                console.error('Error en la búsqueda de clientes:', error);
                $('#clienteSuggestions').empty().hide();
            });
    }

    // Event Listeners
    $('#receptor').on('input', function() {
        clearTimeout(typingTimer);
        if ($(this).val()) {
            typingTimer = setTimeout(buscarClientes, doneTypingInterval);
        } else {
            $('#clienteSuggestions').empty().hide();
        }
    });

    $(document).on('click', function(e) {
        if (!$(e.target).closest('#receptor, #clienteSuggestions').length) {
            $('#clienteSuggestions').hide();
        }
    });

    $('#numero_factura').on('input', function() {
        const value = $(this).val();
        const isValid = /^[0-9]*$/.test(value);
        $(this).toggleClass('is-invalid', !isValid);
        $(this).get(0).setCustomValidity(isValid ? '' : 'Por favor ingrese solo números');
    });

    const $montoTotal = $('#monto_total');

    $montoTotal.on('input', function() {
        if (!validateNumberInput(this.value)) {
            this.value = this.value.replace(/[^\d]/g, '');
        }
    });

    $montoTotal.on('blur', function() {
        if (this.value) {
            const cleanValue = cleanMoney(this.value);
            const number = parseFloat(cleanValue);
            if (!isNaN(number)) {
                this.value = formatMoney(number);
            }
        }
    });

    $montoTotal.on('focus', function() {
        this.value = cleanMoney(this.value);
    });

    // Event listeners para búsqueda de documentos relacionados
    let searchTimeout;
    const triggerSearch = () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            buscarCotizacionesRelacionadas();
            buscarOrdenesCompraRelacionadas();
        }, 500);
    };

    $('#receptor, #monto_total').on('input', triggerSearch);

    // Inicializar búsqueda si hay datos
    if ($('#receptor').val() || $('#monto_total').val()) {
        buscarCotizacionesRelacionadas();
        buscarOrdenesCompraRelacionadas();
    }

    // Manejo del formulario
    $('form').on('submit', function(e) {
        e.preventDefault();
        const montoInput = document.getElementById('monto_total');
        montoInput.value = cleanMoney(montoInput.value);
        this.submit();
    });
});
