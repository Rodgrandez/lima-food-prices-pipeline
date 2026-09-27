# tests/conftest.py
DAY_HTML = (
    "<h1>Lima Metropolitana: Precio Promedio</h1><table><tr class=encabezado><td>Producto</td><td>Variedad</td>"
    "<td class=numero>Precio Promedio</td></tr>"
    "<tr class=contenido><td rowspan=2>Aji Fresco</td><td>Aji Escabeche</td><td class=numero>4.78</td></tr>"
    "<tr class=contenido><td>Aji Monta\u00f1a</td><td class=numero>3.10</td></tr>"
    "<tr class=contenido><td rowspan=1>Ajo</td><td>Ajo Morado</td><td class=numero>6.33</td></tr></table>"
)

INTERVAL_HTML = (
    "<h1>x</h1><table><tr class=encabezado><td rowspan=2>Fecha</td><td colspan=1>Aji Monta&ntilde;a</td>"
    "<td colspan=1>Ajo Morado</td><td colspan=1>Ajo Morado</td></tr>"
    "<tr class=encabezado><td>Precio Promedio (S/. x Kg.)</td><td>Precio Promedio</td><td>Precio Promedio</td></tr>"
    "<tr class=contenido><td>02/01/2025</td><td class=numero>3.38</td><td class=numero>...</td>"
    "<td class=numero>9.99</td></tr>"
    "<tr class=contenido><td>01/01/2025</td><td class=numero>3.25</td><td class=numero>10.50</td>"
    "<td class=numero>1.00</td></tr></table><div class=pieReporte><p>Fuente</p></div>"
)

PRODUCTS_HTML = (
    "<ul><li><input type=checkbox name=productos[] value=0204 id=p0204><label for=p0204>Ajo</label></li>"
    "<li><input type=checkbox name=productos[] value=0202 id=p0202><label for=p0202>Aji fresco</label></li></ul>"
)
