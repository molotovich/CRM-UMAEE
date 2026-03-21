const API_BASE = '/api';

async function fetchProspectos() {
    const res = await fetch(`${API_BASE}/prospectos`);
    const data = await res.json();
    
    let filtered = data.prospectos;
    const role = getCurrentRole();
    if (role === 'VENDEDOR' && currentUser) {
        filtered = data.prospectos.filter(p => p.id_vendedor_asignado == currentUser.id_usuario);
    }
    
    renderKanban(filtered);
}

let allEscuelas = [];

async function fetchEscuelas() {
    const res = await fetch(`${API_BASE}/escuelas`);
    const data = await res.json();
    allEscuelas = data.escuelas;
    
    const datalist = document.getElementById('escuelas-list');
    datalist.innerHTML = '';
    allEscuelas.forEach(e => {
        const opt = document.createElement('option');
        opt.value = e.nombre_escuela;
        datalist.appendChild(opt);
    });
}

// Logic for autocomplete sync
document.getElementById('input-escuela').addEventListener('input', (e) => {
    const val = e.target.value;
    const match = allEscuelas.find(esc => esc.nombre_escuela === val);
    document.getElementById('hidden-id-escuela').value = match ? match.id_escuela : '';
});

// Add school button logic
document.getElementById('add-school-btn').onclick = async () => {
    const name = document.getElementById('input-escuela').value.trim();
    if (!name) return alert("Escribe el nombre de la escuela");
    
    const res = await fetch(`${API_BASE}/escuelas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre_escuela: name })
    });
    
    if (res.ok) {
        const newEsc = await res.json();
        await fetchEscuelas(); // Refresh list
        document.getElementById('input-escuela').value = newEsc.nombre_escuela;
        document.getElementById('hidden-id-escuela').value = newEsc.id_escuela;
        alert("Escuela agregada con éxito");
    }
};

function renderKanban(prospectos) {
    const phases = ['NUEVO', 'CONTACTADO', 'CITA', 'INSCRITO'];
    phases.forEach(phase => {
        const container = document.getElementById(`cards-${phase}`);
        if (!container) return;
        container.innerHTML = '';
        const countBadge = document.getElementById(`count-${phase}`);
        const filtered = prospectos.filter(p => p.fase_crm === phase);
        countBadge.innerText = filtered.length;

        filtered.forEach(p => {
            const card = document.createElement('div');
            card.className = 'prospect-card';
            card.draggable = true;
            card.dataset.id = p.id_prospecto;
            card.innerHTML = `
                <div class="prospect-name">${p.nombre} ${p.apellido_paterno}</div>
                <div class="prospect-meta">${p.email || 'Sin email'}</div>
                <div class="prospect-meta">${p.telefono || 'Sin teléfono'}</div>
                <div class="prospect-meta" style="font-weight:600">${p.escuela || 'Sin escuela'}</div>
                <div class="prospect-origin-tag">${p.origen_prospecto || 'SIN ORIGEN'}</div>
            `;
            
            card.ondragstart = (e) => {
                e.dataTransfer.setData('text/plain', p.id_prospecto);
                card.classList.add('dragging');
            };
            card.ondragend = () => card.classList.remove('dragging');
            
            card.onclick = () => openDetail(p.id_prospecto);
            container.appendChild(card);
        });
    });
}

// Setup Drag and Drop containers
document.querySelectorAll('.kanban-column').forEach(column => {
    column.ondragover = (e) => e.preventDefault();
    column.ondrop = async (e) => {
        e.preventDefault();
        const id = e.dataTransfer.getData('text/plain');
        const newFase = column.dataset.fase;
        
        if (newFase === 'INSCRITO') {
            await openEnrollModal(id);
            return;
        }
        
        await fetch(`${API_BASE}/prospectos/${id}/fase`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fase_crm: newFase })
        });
        fetchProspectos();
    };
});

let currentProspectId = null;
let currentProspectPhone = null;

async function openDetail(id) {
    currentProspectId = id;
    const res = await fetch(`${API_BASE}/prospectos`);
    const data = await res.json();
    const p = data.prospectos.find(x => x.id_prospecto == id);
    currentProspectPhone = p.telefono;
    
    document.getElementById('detail-name').innerText = `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`;
    
    document.getElementById('detail-info-grid').innerHTML = `
        <div><span>Sexo:</span> ${p.sexo || 'N/A'}</div>
        <div><span>Turno:</span> ${p.turno || 'N/A'}</div>
        <div><span>Captura:</span> ${p.fecha_captura || 'N/A'}</div>
        <div><span>Escuela:</span> ${p.escuela || 'Sin escuela'}</div>
        <div><span>Semestre:</span> ${p.semestre || 'N/A'}</div>
        <div><span>Promedio:</span> ${p.promedio || 'N/A'}</div>
        <div><span>Carrera:</span> ${p.carrera_interes || 'N/A'}</div>
        <div><span>Email:</span> ${p.email || 'N/A'}</div>
        <div><span>Teléfono:</span> ${p.telefono || 'N/A'}</div>
        ${p.fase_crm === 'INSCRITO' && p.oferta_carrera ? `
        <div style="grid-column: 1 / -1; background: var(--hover-color, #f1f3f5); padding: 10px; border-radius: 4px; margin-top: 10px;">
            <strong>Inscrito en:</strong> ${p.oferta_carrera} (${p.oferta_periodo} - ${p.oferta_turno || 'N/A'}) - Costo: $${p.oferta_costo}
        </div>` : ''}
        <div class="full-width" style="margin-top: 10px;">
            <button class="btn-primary" onclick="editProspect(${p.id_prospecto})">Editar Detalles</button>
        </div>
    `;
    
    const sRes = await fetch(`${API_BASE}/prospectos/${id}/seguimiento`);
    const sData = await sRes.json();
    
    const timeline = document.getElementById('detail-timeline');
    timeline.innerHTML = sData.seguimientos.map(s => `
        <div class="timeline-item">
            <div class="timeline-date">${new Date(s.fecha_creacion).toLocaleString()} - ${s.tipo_contacto}</div>
            <div>${s.comentarios}</div>
        </div>
    `).join('') || '<p>Sin seguimientos</p>';

    showModal('modal-detail');
}

function showModal(id) {
    document.getElementById('modal-overlay').style.display = 'flex';
    document.getElementById('modal-new-prospect').style.display = id === 'modal-new-prospect' ? 'block' : 'none';
    document.getElementById('modal-detail').style.display = id === 'modal-detail' ? 'block' : 'none';
    document.getElementById('modal-user').style.display = id === 'user-modal' ? 'block' : 'none';
    document.getElementById('modal-enroll').style.display = id === 'modal-enroll' ? 'block' : 'none';
    document.getElementById('modal-new-oferta').style.display = id === 'modal-new-oferta' ? 'block' : 'none';
}

function closeAllModals() {
    document.getElementById('modal-overlay').style.display = 'none';
}

function openNewProspectModal() {
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('field-fecha-captura').value = today;
    
    // Reset form and mode
    const form = document.getElementById('new-prospect-form');
    form.reset();
    form.dataset.mode = 'create';
    delete form.dataset.id;
    
    document.querySelector('#modal-new-prospect h2').innerText = 'Nuevo Prospecto';
    showModal('modal-new-prospect');
}

async function editProspect(id) {
    const res = await fetch(`${API_BASE}/prospectos`);
    const data = await res.json();
    const p = data.prospectos.find(x => x.id_prospecto == id);
    
    const form = document.getElementById('new-prospect-form');
    form.dataset.mode = 'edit';
    form.dataset.id = id;
    
    document.querySelector('#modal-new-prospect h2').innerText = 'Editar Prospecto';
    
    // Fill fields
    form.nombre.value = p.nombre;
    form.apellido_paterno.value = p.apellido_paterno;
    form.apellido_materno.value = p.apellido_materno || '';
    form.sexo.value = p.sexo || 'M';
    form.fecha_captura.value = p.fecha_captura || '';
    form.turno.value = p.turno || 'MATUTINO';
    form.telefono.value = p.telefono || '';
    form.email.value = p.email || '';
    form.semestre.value = p.semestre || '';
    form.promedio.value = p.promedio || '';
    form.carrera_interes.value = p.carrera_interes || '';
    form.origen_prospecto.value = p.origen_prospecto || 'WEB';
    
    // Handle school
    document.getElementById('input-escuela').value = p.escuela || '';
    document.getElementById('hidden-id-escuela').value = p.id_escuela || '';
    
    showModal('modal-new-prospect');
}

document.getElementById('new-prospect-form').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    const mode = e.target.dataset.mode;
    const id = e.target.dataset.id;
    
    const url = mode === 'edit' ? `${API_BASE}/prospectos/${id}` : `${API_BASE}/prospectos`;
    const method = mode === 'edit' ? 'PUT' : 'POST';

    const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    if (res.ok) {
        closeAllModals();
        fetchProspectos();
        if (mode === 'edit') {
            openDetail(id); // Re-open detail to show updated info
        }
    } else {
        alert("Error al guardar prospecto");
    }
};

document.getElementById('new-seguimiento-form').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    await fetch(`${API_BASE}/prospectos/${currentProspectId}/seguimiento`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    openDetail(currentProspectId);
};

function openWhatsApp() {
    let phone = currentProspectPhone;
    if (!phone || phone === 'null') {
        phone = prompt("Ingresa el número (ej: 9981234567)");
    }
    if (phone) {
        // Clean phone: remove non-digits
        const cleanPhone = phone.replace(/\D/g, '');
        const finalPhone = cleanPhone.startsWith('52') ? cleanPhone : '52' + cleanPhone;
        window.open(`https://wa.me/${finalPhone}?text=Hola, te contacto de la UMAEE`, '_blank');
    }
}

async function markAsLost() {
    const reason = prompt("Especifica la razón por la que se marcó como perdido:");
    if (reason === null) return; // Cancelled
    if (!reason.trim()) return alert("Debes especificar una razón.");

    const res = await fetch(`${API_BASE}/prospectos/${currentProspectId}/perdido`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ razon_perdido: reason })
    });

    if (res.ok) {
        closeAllModals();
        fetchProspectos();
    } else {
        alert("Error al actualizar el estado.");
    }
}

function showView(viewId) {
    document.querySelectorAll('.view-container').forEach(v => v.style.display = 'none');
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
    
    document.getElementById(`view-${viewId}`).style.display = 'block';
    const navLink = document.getElementById(`nav-${viewId}`);
    if (navLink) navLink.classList.add('active');
    
    if (viewId === 'dashboard') {
        loadDashboard();
    } else if (viewId === 'usuarios') {
        loadUsuarios();
    } else if (viewId === 'ofertas') {
        loadOfertas();
    } else if (viewId === 'finanzas') {
        loadFinanzas();
    } else if (viewId === 'database') {
        loadDatabase();
    } else if (viewId === 'reportes') {
        loadReportes();
    } else if (viewId === 'kpi') {
        loadKPIs();
    } else {
        fetchProspectos();
    }
}

async function loadUsuarios() {
    const res = await fetch(`${API_BASE}/admin/usuarios`);
    const data = await res.json();
    const tbody = document.getElementById('usuarios-table-body');
    tbody.innerHTML = '';
    
    data.usuarios.forEach(u => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${u.nombre_completo}</td>
            <td>${u.email}</td>
            <td>${u.rol}</td>
            <td>
                <button class="btn-primary" onclick="editUsuario(${u.id_usuario})">Editar</button>
                <button class="btn-danger" onclick="deleteUsuario(${u.id_usuario})">Eliminar</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function openNewUserModal() {
    const form = document.getElementById('user-form');
    form.reset();
    form.dataset.mode = 'create';
    delete form.dataset.id;
    document.getElementById('user-modal-title').innerText = 'Nuevo Usuario';
    showModal('user-modal');
}

async function editUsuario(id) {
    const res = await fetch(`${API_BASE}/admin/usuarios`);
    const data = await res.json();
    const u = data.usuarios.find(x => x.id_usuario == id);
    
    const form = document.getElementById('user-form');
    form.dataset.mode = 'edit';
    form.dataset.id = id;
    document.getElementById('user-modal-title').innerText = 'Editar Usuario';
    
    form.nombre_completo.value = u.nombre_completo;
    form.email.value = u.email;
    form.rol.value = u.rol;
    
    showModal('user-modal');
}

async function deleteUsuario(id) {
    if (!confirm('¿Estás seguro de eliminar este usuario?')) return;
    const res = await fetch(`${API_BASE}/admin/usuarios/${id}`, { method: 'DELETE' });
    if (res.ok) loadUsuarios();
}

document.getElementById('user-form').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    const mode = e.target.dataset.mode;
    const id = e.target.dataset.id;
    
    const url = mode === 'edit' ? `${API_BASE}/admin/usuarios/${id}` : `${API_BASE}/admin/usuarios`;
    const method = mode === 'edit' ? 'PUT' : 'POST';

    const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    if (res.ok) {
        closeAllModals();
        loadUsuarios();
    } else {
        alert("Error al guardar usuario");
    }
};


async function loadDashboard() {
    const res = await fetch(`${API_BASE}/admin/dashboard`);
    const data = await res.json();
    const stats = data.stats;
    
    const container = document.getElementById('dashboard-stats');
    container.innerHTML = '';
    
    const phases = ['NUEVO', 'CONTACTADO', 'CITA', 'INSCRITO', 'PERDIDO'];
    
    phases.forEach(phase => {
        const count = stats[phase] || 0;
        const card = document.createElement('div');
        card.className = `stat-card ${phase === 'PERDIDO' ? 'perdido' : ''}`;
        card.innerHTML = `
            <h3>${phase}</h3>
            <div class="value">${count}</div>
        `;
        card.onclick = () => loadProspectList(phase);
        container.appendChild(card);
    });
}

async function loadProspectList(fase) {
    const res = await fetch(`${API_BASE}/admin/prospectos/${fase}`);
    const data = await res.json();
    
    document.getElementById('table-title').innerText = `Prospectos en estado: ${fase}`;
    const tbody = document.getElementById('prospectos-table-body');
    tbody.innerHTML = '';
    
    data.prospectos.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.nombre}</td>
            <td>${p.carrera_interes || 'N/A'}</td>
            <td>${p.vendedor_nombre}</td>
            <td>${p.ultimo_seguimiento ? new Date(p.ultimo_seguimiento).toLocaleString() : 'Sin seguimiento'}</td>
            <td>
                <button class="btn-primary" onclick="openDetail(${p.id_prospecto})">Ver Ficha</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    document.getElementById('prospect-list-section').style.display = 'block';
    window.scrollTo({ top: document.getElementById('prospect-list-section').offsetTop - 50, behavior: 'smooth' });
}

function hideProspectList() {
    document.getElementById('prospect-list-section').style.display = 'none';
}

// App initialization moved to checkLoginState / initApp

// Ofertas Académicas Logic
let allOfertas = [];

async function loadOfertas() {
    const resCarreras = await fetch(`${API_BASE}/admin/carreras`);
    const dataCarreras = await resCarreras.json();
    const tbodyCarreras = document.getElementById('carreras-table-body');
    tbodyCarreras.innerHTML = dataCarreras.carreras.map(c => `<tr><td>${c.id_carrera}</td><td>${c.nombre}</td></tr>`).join('');
    
    document.getElementById('oferta-carrera-select').innerHTML = 
        `<option value="ALL">-- Todas las Carreras --</option>` + 
        dataCarreras.carreras.map(c => `<option value="${c.id_carrera}">${c.nombre}</option>`).join('');

    const resPeriodos = await fetch(`${API_BASE}/admin/periodos`);
    const dataPeriodos = await resPeriodos.json();
    const tbodyPeriodos = document.getElementById('periodos-table-body');
    tbodyPeriodos.innerHTML = dataPeriodos.periodos.map(p => `<tr><td>${p.id_periodo}</td><td>${p.nombre}</td></tr>`).join('');

    document.getElementById('oferta-periodo-select').innerHTML = dataPeriodos.periodos.map(p => `<option value="${p.id_periodo}">${p.nombre}</option>`).join('');

    const resTurnos = await fetch(`${API_BASE}/admin/turnos`);
    const dataTurnos = await resTurnos.json();
    const tbodyTurnos = document.getElementById('turnos-table-body');
    if (tbodyTurnos) tbodyTurnos.innerHTML = dataTurnos.turnos.map(t => `<tr><td>${t.id_turno}</td><td>${t.nombre}</td></tr>`).join('');
    
    const ofertaTurnoSelect = document.getElementById('oferta-turno-select');
    if (ofertaTurnoSelect) ofertaTurnoSelect.innerHTML = dataTurnos.turnos.map(t => `<option value="${t.id_turno}">${t.nombre}</option>`).join('');

    const resOfertas = await fetch(`${API_BASE}/admin/ofertas`);
    const dataOfertas = await resOfertas.json();
    allOfertas = dataOfertas.ofertas;
    
    const tbodyOfertas = document.getElementById('ofertas-table-body');
    const role = getCurrentRole();
    tbodyOfertas.innerHTML = dataOfertas.ofertas.map(o => `
        <tr>
            <td>${o.carrera_nombre}</td>
            <td>${o.periodo_nombre}</td>
            <td>${o.turno_nombre || 'N/A'}</td>
            <td>$${o.costo}</td>
            <td>
                ${role === 'SUPERADMIN' ? `
                <button class="btn-primary" onclick="editOferta(${o.id_oferta})" style="padding: 4px 8px; font-size: 0.8rem;">Editar</button>
                <button class="btn-danger" onclick="deleteOferta(${o.id_oferta})" style="padding: 4px 8px; font-size: 0.8rem;">Eliminar</button>
                ` : '-'}
            </td>
        </tr>
    `).join('');
}

function openNewOfertaModal() {
    document.getElementById('new-oferta-form').reset();
    showModal('modal-new-oferta');
}

document.getElementById('new-oferta-form').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    const res = await fetch(`${API_BASE}/admin/ofertas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (res.ok) {
        closeAllModals();
        loadOfertas();
    }
};

async function crearCarrera() {
    const input = document.getElementById('nueva-carrera-input');
    const val = input.value.trim();
    if (!val) return;
    await fetch(`${API_BASE}/admin/carreras`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({nombre: val})
    });
    input.value = '';
    loadOfertas();
}

async function crearPeriodo() {
    const input = document.getElementById('nuevo-periodo-input');
    const val = input.value.trim();
    if (!val) return;
    await fetch(`${API_BASE}/admin/periodos`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({nombre: val})
    });
    input.value = '';
    loadOfertas();
}

async function crearTurno() {
    const input = document.getElementById('nuevo-turno-input');
    const val = input.value.trim();
    if (!val) return;
    const res = await fetch(`${API_BASE}/admin/turnos`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Role': getCurrentRole()
        },
        body: JSON.stringify({nombre: val})
    });
    if (res.status === 403) {
        const err = await res.json();
        alert(err.error);
        return;
    }
    input.value = '';
    loadOfertas();
}

let currentUser = null;

function getCurrentRole() {
    return currentUser ? currentUser.rol : 'VENDEDOR';
}

document.getElementById('login-form').onsubmit = async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    const res = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });
    
    if (res.ok) {
        document.getElementById('login-error').style.display = 'none';
        currentUser = await res.json();
        localStorage.setItem('crm_user', JSON.stringify(currentUser));
        initApp();
    } else {
        document.getElementById('login-error').style.display = 'block';
    }
};

async function logout() {
    await fetch(`${API_BASE}/logout`, { method: 'POST' });
    localStorage.removeItem('crm_user');
    currentUser = null;
    window.location.reload();
}

function initApp() {
    document.getElementById('view-login').style.display = 'none';
    document.getElementById('main-app').style.display = 'block';
    document.getElementById('user-display-name').innerText = currentUser.nombre_completo;
    
    updateUIForRole();
    fetchProspectos();
    fetchEscuelas();
}

function checkLoginState() {
    const stored = localStorage.getItem('crm_user');
    if (stored) {
        try {
            currentUser = JSON.parse(stored);
            initApp();
        } catch (e) {
            console.error('Error parsing stored user', e);
        }
    }
}

// Start app Check
checkLoginState();

function updateUIForRole() {
    const role = getCurrentRole();
    
    const navDashboard = document.getElementById('nav-dashboard');
    const navUsuarios = document.getElementById('nav-usuarios');
    const navOfertas = document.getElementById('nav-ofertas');
    const navFinanzas = document.getElementById('nav-finanzas');
    const navReportes = document.getElementById('nav-reportes');
    const navDatabase = document.getElementById('nav-database');
    const navKpi = document.getElementById('nav-kpi');
    
    // Hide all initially
    if(navDashboard) navDashboard.style.display = 'none';
    if(navUsuarios) navUsuarios.style.display = 'none';
    if(navOfertas) navOfertas.style.display = 'none';
    if(navDatabase) navDatabase.style.display = 'none';
    if(navReportes) navReportes.style.display = 'none';
    if(navFinanzas) navFinanzas.style.display = 'none';
    if(navKpi) navKpi.style.display = 'none';
    
    if (role === 'SUPERADMIN') {
        if(navDashboard) navDashboard.style.display = 'inline-block';
        if(navUsuarios) navUsuarios.style.display = 'inline-block';
        if(navOfertas) navOfertas.style.display = 'inline-block';
        if(navDatabase) navDatabase.style.display = 'inline-block';
        if(navReportes) navReportes.style.display = 'inline-block';
        if(navFinanzas) navFinanzas.style.display = 'inline-block';
        if(navKpi) navKpi.style.display = 'inline-block';
    } else if (role === 'ADMIN') {
        if(navDashboard) navDashboard.style.display = 'inline-block';
        if(navOfertas) navOfertas.style.display = 'inline-block';
        if(navDatabase) navDatabase.style.display = 'inline-block';
        if(navReportes) navReportes.style.display = 'inline-block';
        if(navFinanzas) navFinanzas.style.display = 'inline-block';
        if(navKpi) navKpi.style.display = 'inline-block';
    }
    
    // If the user's current view is no longer accessible, force back to Kanban
    const currentActive = document.querySelector('.nav-links a.active');
    if (currentActive && currentActive.style.display === 'none') {
        showView('kanban');
    }
    
    // Hide Turno Add container for non-superadmin
    const turnoAddContainer = document.getElementById('turno-add-container');
    if (turnoAddContainer) {
        turnoAddContainer.style.display = role === 'SUPERADMIN' ? 'flex' : 'none';
    }
    
    // Handle Oferta Config button visibility
    const btnToggleConfig = document.getElementById('btn-toggle-config');
    const ofertaConfigContainer = document.getElementById('oferta-config-container');
    if (btnToggleConfig) {
        if (role === 'SUPERADMIN' || role === 'ADMIN') {
            btnToggleConfig.style.display = 'inline-block';
        } else {
            btnToggleConfig.style.display = 'none';
            if (ofertaConfigContainer) ofertaConfigContainer.style.display = 'none';
        }
    }
    
    // Re-render stuff that depends on role
    loadOfertas();
}

function toggleOfertaConfig() {
    const container = document.getElementById('oferta-config-container');
    if (container.style.display === 'none') {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

// Set up UI initially handled by checkLoginState

async function deleteOferta(id) {
    if (!confirm('¿Seguro que deseas eliminar esta oferta?')) return;
    const res = await fetch(`${API_BASE}/admin/ofertas/${id}`, {
        method: 'DELETE',
        headers: { 'X-Role': getCurrentRole() }
    });
    if (res.status === 403) {
        const err = await res.json();
        alert(err.error);
        return;
    }
    if (res.ok) {
        loadOfertas();
    }
}

async function editOferta(id) {
    const newCost = prompt('Ingresa el nuevo costo para la oferta:');
    if (!newCost) return;
    
    const costValue = parseFloat(newCost);
    if (isNaN(costValue)) return alert('Costo inválido');

    const res = await fetch(`${API_BASE}/admin/ofertas/${id}`, {
        method: 'PUT',
        headers: { 
            'Content-Type': 'application/json',
            'X-Role': getCurrentRole() 
        },
        body: JSON.stringify({ costo: costValue })
    });
    
    if (res.status === 403) {
        const err = await res.json();
        alert(err.error);
        return;
    }
    if (res.ok) {
        loadOfertas();
    }
}

// Enrollment Logic
let enrollProspectId = null;

async function openEnrollModal(id) {
    enrollProspectId = id;
    
    const res = await fetch(`${API_BASE}/admin/ofertas`);
    const data = await res.json();
    allOfertas = data.ofertas;
    
    document.getElementById('enroll-oferta-select').innerHTML = allOfertas.map(o => 
        `<option value="${o.id_oferta}">${o.carrera_nombre} - ${o.periodo_nombre} - ${o.turno_nombre || 'N/A'} ($${o.costo})</option>`
    ).join('');
    
    showModal('modal-enroll');
}

document.getElementById('enroll-form').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    const res = await fetch(`${API_BASE}/prospectos/${enrollProspectId}/fase`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            fase_crm: 'INSCRITO',
            id_oferta_inscripcion: data.id_oferta_inscripcion
        })
    });
    
    if (res.ok) {
        closeAllModals();
        fetchProspectos();
    }
};


// --- Finanzas Logic ---
let finanzasData = [];

async function loadFinanzas() {
    const res = await fetch(`${API_BASE}/admin/finanzas`, {
        headers: { 'X-Role': getCurrentRole() }
    });
    if (res.status === 403) return;
    const data = await res.json();
    finanzasData = data.finanzas;
    
    // Populate the filter dropdown if empty
    const select = document.getElementById('finanzas-periodo-filter');
    if (select && select.options.length <= 1) {
        const uniquePeriodos = [...new Set(finanzasData.map(f => f.periodo_nombre))].sort();
        uniquePeriodos.forEach(pName => {
            if (!pName) return;
            const opt = document.createElement('option');
            opt.value = pName;
            opt.textContent = pName;
            select.appendChild(opt);
        });
    }

    renderFinanzas();
}

function renderFinanzas() {
    const select = document.getElementById('finanzas-periodo-filter');
    const filterValue = select ? select.value : 'ALL';
    
    let totalEsperado = 0;
    const tbody = document.getElementById('finanzas-table-body');
    
    const filtered = finanzasData.filter(f => filterValue === 'ALL' || f.periodo_nombre === filterValue);
    
    tbody.innerHTML = filtered.map(f => {
        totalEsperado += f.monto_esperado;
        return `
        <tr>
            <td>${f.carrera_nombre}</td>
            <td>${f.periodo_nombre}</td>
            <td>${f.turno_nombre || 'N/A'}</td>
            <td>$${f.costo.toLocaleString()}</td>
            <td>${f.num_inscritos}</td>
            <td>$${f.monto_esperado.toLocaleString()}</td>
        </tr>`;
    }).join('');
    
    document.getElementById('monto-total-esperado').innerText = `$${totalEsperado.toLocaleString()}`;
}

// --- KPI Logic ---

async function loadKPIs() {
    // Load vendors for select
    const resUsers = await fetch(`${API_BASE}/admin/usuarios`);
    if (resUsers.ok) {
        const dataUsers = await resUsers.json();
        const vendedores = dataUsers.usuarios.filter(u => u.rol === 'VENDEDOR');
        document.getElementById('kpi-vendedor-select').innerHTML = vendedores.map(v => 
            `<option value="${v.id_usuario}">${v.nombre_completo}</option>`
        ).join('');
    }
    
    // Set default month to current
    const today = new Date();
    const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
    const mesInput = document.getElementById('kpi-mes-input');
    const reporteMesInput = document.getElementById('reporte-mes-input');
    if(mesInput && !mesInput.value) mesInput.value = currentMonth;
    if(reporteMesInput && !reporteMesInput.value) reporteMesInput.value = currentMonth;
    
    loadKPIReporte();
}

async function loadKPIReporte() {
    const mes = document.getElementById('reporte-mes-input').value;
    if (!mes) return;
    
    const res = await fetch(`${API_BASE}/admin/kpi/reporte?mes=${mes}`, {
        headers: { 'X-Role': getCurrentRole() }
    });
    if (res.status === 403) return;
    
    const data = await res.json();
    const tbody = document.getElementById('kpi-reporte-body');
    
    tbody.innerHTML = data.reporte.map(r => {
        const pctContactos = r.meta_contactos > 0 ? Math.round((r.real_contactos / r.meta_contactos) * 100) : 0;
        const pctInscritos = r.meta_inscritos > 0 ? Math.round((r.real_inscritos / r.meta_inscritos) * 100) : 0;
        
        return `
        <tr>
            <td>${r.vendedor_nombre}</td>
            <td>${r.mes}</td>
            <td>
                <b>${r.real_contactos}</b> / ${r.meta_contactos} 
                <span style="color: ${pctContactos >= 100 ? 'var(--success-color, green)' : 'orange'}; font-size: 0.8em; margin-left: 4px;">(${pctContactos}%)</span>
            </td>
            <td>
                <b>${r.real_inscritos}</b> / ${r.meta_inscritos}
                <span style="color: ${pctInscritos >= 100 ? 'var(--success-color, green)' : 'orange'}; font-size: 0.8em; margin-left: 4px;">(${pctInscritos}%)</span>
            </td>
        </tr>`;
    }).join('');
}

const kpiForm = document.getElementById('kpi-meta-form');
if (kpiForm) {
    kpiForm.onsubmit = async (e) => {
        e.preventDefault();
        const id_usuario = document.getElementById('kpi-vendedor-select').value;
        const mes = document.getElementById('kpi-mes-input').value;
        const contactos = parseInt(document.getElementById('kpi-meta-contactos').value);
        const inscritos = parseInt(document.getElementById('kpi-meta-inscritos').value);
        
        const res = await fetch(`${API_BASE}/admin/kpi/metas`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Role': getCurrentRole()
            },
            body: JSON.stringify({
                id_usuario: id_usuario,
                periodo_mes: mes,
                meta_contactos: contactos,
                meta_inscritos: inscritos
            })
        });
        
        if (res.ok) {
            alert('Meta guardada exitosamente');
            // Check if looking at same month to refresh report
            if (document.getElementById('reporte-mes-input').value === mes) {
                loadKPIReporte();
            }
        } else {
            alert('Error al guardar meta');
        }
    };
}

// --- Reportes Logic ---

async function loadReportes() {
    // Populate vendedores and escuelas if not yet done
    const vSelect = document.getElementById('filtro-vendedor');
    if (vSelect && vSelect.options.length <= 1) {
        const res = await fetch(`${API_BASE}/admin/usuarios`);
        if (res.ok) {
            const data = await res.json();
            data.usuarios.forEach(u => {
                if(u.rol === 'VENDEDOR' || u.rol === 'ADMIN' || u.rol === 'SUPERADMIN') {
                    const opt = document.createElement('option');
                    opt.value = u.id_usuario;
                    opt.textContent = u.nombre_completo;
                    vSelect.appendChild(opt);
                }
            });
        }
    }

    const eSelect = document.getElementById('filtro-escuela');
    if (eSelect && eSelect.options.length <= 1) {
        if (!allEscuelas || allEscuelas.length === 0) {
            const res = await fetch(`${API_BASE}/escuelas`);
            if (res.ok) {
                const data = await res.json();
                allEscuelas = data.escuelas;
            }
        }
        allEscuelas.forEach(e => {
            const opt = document.createElement('option');
            opt.value = e.id_escuela;
            opt.textContent = e.nombre_escuela;
            eSelect.appendChild(opt);
        });
    }

    // Auto-fetch with no filters on load
    fetchPrevisualizacionReporte();
}

function buildQueryParamsReportes() {
    const form = document.getElementById('filtro-reportes-form');
    if (!form) return '';
    const data = new FormData(form);
    const params = new URLSearchParams();
    for (const [k, v] of data.entries()) {
        if (v) params.append(k, v);
    }
    return params.toString();
}

async function fetchPrevisualizacionReporte() {
    const qs = buildQueryParamsReportes();
    const res = await fetch(`${API_BASE}/reportes/prospectos?${qs}`);
    if (!res.ok) return alert('Error al cargar reporte');
    
    const data = await res.json();
    const tbody = document.getElementById('reportes-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    if (data.prospectos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No se encontraron resultados</td></tr>';
        return;
    }
    
    data.prospectos.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.nombre_solo} ${p.apellido_paterno}</td>
            <td><span class="view-pill status-${p.fase_crm ? p.fase_crm.toLowerCase() : 'nuevo'}">${p.fase_crm}</span></td>
            <td>${p.escuela || '-'}</td>
            <td>${p.promedio || '-'}</td>
            <td>${p.vendedor_nombre || 'N/A'}</td>
            <td>${p.ultimo_seguimiento ? new Date(p.ultimo_seguimiento).toLocaleDateString() : 'N/A'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function descargarReporte(formato) {
    const qs = buildQueryParamsReportes();
    const url = `${API_BASE}/reportes/prospectos/${formato}?${qs}`;
    window.open(url, '_blank');
}

/* --- Base de Datos Logic --- */

let allProspectsDB = [];
let allVendedores = [];

async function loadDatabase() {
    // Check access
    const role = getCurrentRole();
    if (role !== 'ADMIN' && role !== 'SUPERADMIN') return;

    // Load Vendedores if not yet done
    if (allVendedores.length === 0) {
        const res = await fetch(`${API_BASE}/admin/usuarios`);
        if (res.ok) {
            const data = await res.json();
            allVendedores = data.usuarios.filter(u => u.rol === 'VENDEDOR' || u.rol === 'ADMIN' || u.rol === 'SUPERADMIN');
            
            const vFilter = document.getElementById('db-vendedor-filter');
            if(vFilter) {
                // Keep the first two options (All, None)
                vFilter.innerHTML = '<option value="ALL">Cualquier Ejecutivo</option><option value="NONE">Sin Asignar</option>';
                allVendedores.forEach(v => {
                    const opt = document.createElement('option');
                    opt.value = v.id_usuario;
                    opt.textContent = v.nombre_completo;
                    vFilter.appendChild(opt);
                });
            }
        }
    }

    // Load all prospects via report endpoint (full dump)
    const resAll = await fetch(`${API_BASE}/reportes/prospectos`); 
    const data = await resAll.json();
    allProspectsDB = data.prospectos;
    
    renderDatabaseItems();
}

function renderDatabaseItems() {
    const search = document.getElementById('db-search-input').value.toLowerCase();
    const vendedorId = document.getElementById('db-vendedor-filter').value;
    
    const tbody = document.getElementById('database-table-body');
    if (!tbody) return;
    
    const filtered = allProspectsDB.filter(p => {
        const nameFull = p.nombre || '';
        const matchesSearch = nameFull.toLowerCase().includes(search);
        const matchesVendedor = vendedorId === 'ALL' || 
                                (vendedorId === 'NONE' && !p.id_vendedor_asignado) || 
                                (p.id_vendedor_asignado == vendedorId);
        return matchesSearch && matchesVendedor;
    });
    
    tbody.innerHTML = filtered.map(p => `
        <tr>
            <td>${p.id_prospecto}</td>
            <td>${p.nombre}</td>
            <td><span class="badge" style="background:rgba(255,255,255,0.05); color:var(--text-muted);">${p.fase_crm}</span></td>
            <td>
                <select onchange="reassignVendedor(${p.id_prospecto}, this.value)" style="padding: 0.2rem; background: rgba(0,0,0,0.2);">
                    <option value="">Sin Asignar</option>
                    ${allVendedores.map(v => `<option value="${v.id_usuario}" ${p.id_vendedor_asignado == v.id_usuario ? 'selected' : ''}>${v.nombre_completo}</option>`).join('')}
                </select>
            </td>
            <td>
                <button class="btn-primary" onclick="openDetail(${p.id_prospecto})" style="padding: 2px 8px; font-size: 0.75rem;">Detalle</button>
            </td>
        </tr>
    `).join('');
}

async function repartirEquitativo() {
    if (!confirm("¿Estás seguro de repartir todos los prospectos sin asignar equitativamente entre los vendedores?")) return;
    
    const res = await fetch(`${API_BASE}/admin/prospectos/repartir-equitativo`, {
        method: 'POST',
        headers: { 'X-Role': getCurrentRole() }
    });
    
    const data = await res.json();
    if (res.ok) {
        alert(data.message);
        loadDatabase();
    } else {
        alert("Error: " + (data.error || "Ocurrió un problema"));
    }
}

async function reassignVendedor(prospectoId, vendedorId) {
    const res = await fetch(`${API_BASE}/admin/prospectos/${prospectoId}/vendedor`, {
        method: 'PATCH',
        headers: { 
            'Content-Type': 'application/json',
            'X-Role': getCurrentRole()
        },
        body: JSON.stringify({ id_vendedor_asignado: vendedorId || null })
    });
    
    if (res.ok) {
        // Update local data for immediate UI consistency
        const p = allProspectsDB.find(x => x.id_prospecto == prospectoId);
        if (p) p.id_vendedor_asignado = vendedorId;
        console.log(`Prospecto ${prospectoId} reasignado a ${vendedorId}`);
    } else {
        alert("Error al reasignar ejecutivo");
    }
}

async function handleBulkUpload(input) {
    const file = input.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await fetch(`${API_BASE}/admin/prospectos/upload`, {
        method: 'POST',
        headers: { 'X-Role': getCurrentRole() },
        body: formData
    });
    
    if (res.ok) {
        const result = await res.json();
        let msg = `Éxito: ${result.imported} prospectos importados.`;
        
        if (result.errors && result.errors.length > 0) {
            msg += `\n\nNo se subieron ${result.errors.length} registros. Se descargará un reporte con los detalles.`;
            
            // Generate CSV for errors
            const headers = ['Fila', 'Nombre', 'Motivo/Error'];
            const rows = result.errors.map(e => [e.fila, e.nombre || '', e.motivo || e.error]);
            const csvContent = [headers, ...rows].map(r => r.join(',')).join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `errores_importacion_${new Date().getTime()}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        alert(msg);
        loadDatabase();
    } else {
        const err = await res.json();
        alert("Error en la subida: " + (err.error || "Formato inválido"));
    }
    input.value = ''; // Reset input
}
