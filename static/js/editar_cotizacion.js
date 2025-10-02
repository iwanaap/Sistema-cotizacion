$(document).ready(function () {
    let hasUnsavedChanges = false;
    let isSubmitting = false;

    // Función para marcar que hay cambios sin guardar
    function markAsChanged() {
        hasUnsavedChanges = true;
    }

    // Función para formatear valores con "$" y separador de miles con punto
    function formatMoney(value) {
        let number = parseFloat(value) || 0;
        return "$" + number.toLocaleString("es-CL");
    }

    // Función para limpiar el formato antes de realizar cálculos
    function cleanMoney(value) {
        return parseFloat(value.replace(/\./g, "").replace("$", "").replace(",", ".")) || 0;
    }

    function actualizarProductosInput() {
        var productos = [];
        var totalNeto = 0;
        var totalCosto = 0;
        
        $("#productosTable tbody tr").each(function () {
            var producto = $(this).find(".producto").val();
            var cantidad = parseFloat($(this).find(".cantidad").val()) || 0;
            var formato = $(this).find(".formato").val();
            var precio = cleanMoney($(this).find(".precio").val()) || 0;
            var costo = cleanMoney($(this).find(".costo").val()) || 0;
            var link = $(this).find(".link").val();
            var subtotal = cantidad * precio;
            var subtotalCosto = cantidad * costo;
            var imagenActualInput = $(this).find(".imagen-actual");
            var imagenNombre = '';
            
            if (imagenActualInput.length > 0) {
                // Mantener la imagen existente
                imagenNombre = imagenActualInput.val();
            } else {
                // Verificar si hay una nueva imagen seleccionada
                var fileInput = $(this).find(".producto-imagen")[0];
                if (fileInput && fileInput.files[0]) {
                    imagenNombre = ''; // Se actualizará en el backend
                }
            }

            totalNeto += subtotal;
            totalCosto += subtotalCosto;

            $(this).find(".subtotal").text(formatMoney(subtotal)); // Mostrar subtotal con formato

            productos.push({
                producto: producto,
                cantidad: cantidad,
                formato: formato,
                precio: precio,  // Guardar sin formato
                subtotal: subtotal,  // Guardar sin formato
                costo: costo,  // Guardar sin formato
                link: link,
                subtotalCosto: subtotalCosto,
                imagen: imagenNombre
            });
        });

        $("#productosInput").val(JSON.stringify(productos));

        var iva = totalNeto * 0.19;
        var total = totalNeto + iva;
        var gananciaTotal = totalNeto - totalCosto;
        var ivaCompra = totalCosto * 0.19;
        var gananciaTotalRestaIva = gananciaTotal - (iva - (totalCosto * 0.19));

        $("#totalNeto").text(formatMoney(totalNeto));
        $("#iva").text(formatMoney(iva));
        $("#total").text(formatMoney(total));
        $("#totalCosto").text(formatMoney(totalCosto));
        $("#gananciaTotal").text(formatMoney(gananciaTotal));
        $("#ivaCompra").text(formatMoney(ivaCompra));
        $("#gananciaTotalRestaIva").text(formatMoney(gananciaTotalRestaIva));
    }

    // Manejar la previsualización de imágenes
    $("#productosTable").on("change", ".producto-imagen", function(e) {
        const file = e.target.files[0];
        const container = $(this).siblings('.image-preview-container');
        const imgPreview = container.find('.imagen-preview');
        const deleteBtn = container.find('.eliminar-imagen');
        const imagenActual = container.find('.imagen-actual');
        
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imgPreview.attr('src', e.target.result);
                imgPreview.show();
                if (!deleteBtn.length) {
                    container.append('<button type="button" class="btn btn-danger btn-sm eliminar-imagen" style="position: absolute; top: 0; right: 0; padding: 2px 5px;"><i class="bi bi-x"></i></button>');
                }
                imagenActual.remove();
            };
            reader.readAsDataURL(file);
        } else {
            imgPreview.attr('src', '#');
            imgPreview.hide();
            deleteBtn.remove();
        }
    });

    // Manejar la eliminación de imágenes
    $("#productosTable").on("click", ".eliminar-imagen", function(e) {
        e.preventDefault();
        const container = $(this).closest('.image-preview-container');
        const imgPreview = container.find('.imagen-preview');
        const fileInput = container.closest('.image-upload').find('.producto-imagen');
        const imagenActual = container.find('.imagen-actual');

        fileInput.val('');
        imgPreview.attr('src', '#');
        imgPreview.hide();
        $(this).remove();
        imagenActual.remove();
        actualizarProductosInput();
    });

    // Evento para agregar una nueva fila de producto
    $("#agregarProducto").click(function () {
        var nuevaFila = `
            <tr>
                <td>
                    <div class="image-upload">
                        <input type="file" class="form-control producto-imagen" accept="image/*">
                        <img class="imagen-preview" src="#" style="max-width: 100px; max-height: 100px; display: none;">
                    </div>
                </td>
                <td><input type="text" class="form-control producto" required></td>
                <td><input type="number" class="form-control cantidad" required></td>
                <td><input type="text" class="form-control formato"></td>
                <td><input type="text" class="form-control precio money-input" placeholder="$0" required></td>
                <td class="subtotal">$0</td>
                <td><input type="text" class="form-control costo money-input" placeholder="$0"></td>
                <td><input type="text" class="form-control link"></td>
                <td><button type="button" class="btn btn-danger eliminarProducto">Eliminar</button></td>
            </tr>`;
        $("#productosTable tbody").append(nuevaFila);
    });

    // Eventos para la tabla de productos
    $("#productosTable")
        .on("click", ".eliminarProducto", function () {
            $(this).closest("tr").remove();
            actualizarProductosInput();
        })
        .on("input", ".producto, .cantidad, .formato, .precio, .costo, .link", function () {
            actualizarProductosInput();
        })
        .on("blur", ".money-input", function () {
            let value = cleanMoney(this.value);
            if (value > 0) {
                this.value = formatMoney(value);
            } else {
                this.value = "";
            }
            actualizarProductosInput();
        })
        .on("focus", ".money-input", function () {
            this.value = cleanMoney(this.value);
        });

    // Manejo del formulario
    $("form").on("submit", function (e) {
        e.preventDefault();
        isSubmitting = true;
        
        var formData = new FormData(this);
        formData.delete('productos');
        
        var productos = [];
        $("#productosTable tbody tr").each(function(index) {
            var row = $(this);
            var producto = {
                producto: row.find(".producto").val(),
                cantidad: parseFloat(row.find(".cantidad").val()) || 0,
                formato: row.find(".formato").val(),
                precio: cleanMoney(row.find(".precio").val()),
                costo: cleanMoney(row.find(".costo").val()),
                link: row.find(".link").val(),
                subtotal: (parseFloat(row.find(".cantidad").val()) || 0) * cleanMoney(row.find(".precio").val()),
                subtotalCosto: (parseFloat(row.find(".cantidad").val()) || 0) * cleanMoney(row.find(".costo").val())
            };

            // Manejar imágenes
            var fileInput = row.find(".producto-imagen")[0];
            var imagenActual = row.find(".imagen-actual");
            var imagenPreview = row.find(".imagen-preview");
            
            if (fileInput && fileInput.files[0]) {
                formData.append('producto_imagen_' + index, fileInput.files[0]);
                producto.imagen = '';
            } else if (imagenActual.length > 0 && imagenActual.val()) {
                producto.imagen = imagenActual.val();
            } else if (imagenPreview.attr('src') && !imagenPreview.attr('src').startsWith('#')) {
                var imgSrc = imagenPreview.attr('src');
                var imgName = imgSrc.split('/').pop();
                producto.imagen = imgName;
            } else {
                producto.imagen = '';
                formData.append('imagen_eliminada_' + index, 'true');
            }

            productos.push(producto);
        });
        
        formData.append('productos', JSON.stringify(productos));
        
        var submitButton = $(this).find('button[type="submit"]');
        var originalText = submitButton.text();
        submitButton.prop('disabled', true).text('Guardando...');
        
        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                window.location.href = '/';
            },
            error: function(xhr, status, error) {
                console.error('Error al guardar:', error);
                alert('Error al guardar los cambios. Por favor, intente nuevamente.');
                submitButton.prop('disabled', false).text(originalText);
            }
        });
    });

    // Inicialización
    actualizarProductosInput();

    // Detectar cambios en el formulario
    $('form input, form textarea, form select').on('input change', function() {
        markAsChanged();
    });

    // Detectar cuando se agregan o eliminan productos
    $(document).on('click', '.btn-danger', function() {
        markAsChanged();
    });

    $(document).on('click', '#agregarProducto', function() {
        markAsChanged();
    });

    // Evento para detectar cuando se intenta salir de la página
    $(window).on('beforeunload', function() {
        if (hasUnsavedChanges && !isSubmitting) {
            return 'ATENCIÓN: Estás saliendo y no has guardado los cambios. ¿Realmente quieres salir?';
        }
    });

    // Marcar que se está enviando el formulario para evitar la alerta
    $('form').on('submit', function() {
        isSubmitting = true;
    });
});
