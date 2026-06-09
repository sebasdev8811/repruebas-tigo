// API Configuration
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : window.location.origin;

// State Management
const appState = {
    user: null,
    token: localStorage.getItem('token'),
    isLoggedIn: !!localStorage.getItem('token'),
    uploadedFile: null,
    uploadCompleted: false,
    fallasMasivas: [],
    gestionesMap: {},
    repruebasMap: {},
    gestionModalData: null,
    garantiaPendientes: [],
    garantiaClienteMap: {},
    garantiaModalData: null,
    exportFormat: 'pdf',
    activeMetric: 'repruebas',
    rol: localStorage.getItem('userRole') || null,
    mustChangePassword: localStorage.getItem('mustChangePassword') === 'true',
    passwordChangeModalRequired: false,
    errorMessage: null
};

const FILE_CONFIG = {
    maxSize: 10 * 1024 * 1024,
    allowedTypes: [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
};

const ANALISTA_ESTADOS = ['OK', 'Falla física', 'Falla lógica', 'Sin reprueba', 'Falla física lógica'];

const ANALISTA_COLORES = {
    'OK': '#27ae60',
    'Sin reprueba': '#95a5a6',
    'Falla física': '#f39c12',
    'Falla lógica': '#f1c40f',
    'Falla física lógica': '#e74c3c'
};

const ELEMENTO_LABELS = {
    nodo: 'Nodo',
    cmts: 'CMTS',
    amplificador: 'Amplificador',
    tap: 'TAP'
};

const ESTADO_GESTION_LABELS = {
    no_gestionado: 'No gestionado',
    gestionado: 'Gestionado',
    escalado: 'Escalado'
};

const ESTADO_GARANTIA_LABELS = {
    escalada: 'Escalada',
    no_escalada: 'No escalada',
    pendiente: 'Pendiente'
};

const METRIC_DATA = {
    repruebas: {
        dashboardTrendLabel: 'Repruebas',
        dashboardTrend: [85, 92, 78, 110, 95, 130, 142, 155],
        dashboardChartTitle: 'Tendencia mensual de repruebas',
        alertTitle: '🚨 Alertas de fallas masivas - Repruebas'
    },
    garantias: {
        dashboardTrendLabel: 'Garantías',
        dashboardTrend: [12, 18, 15, 22, 27, 30, 34, 38],
        dashboardChartTitle: 'Tendencia mensual de garantías',
        alertTitle: '🚨 Alertas de fallas masivas - Garantías'
    }
};

const DOM = {
    loginForm: document.getElementById('loginForm'),
    loginScreen: document.getElementById('loginScreen'),
    appScreen: document.getElementById('appScreen'),
    userMenuButton: document.getElementById('userMenuButton'),
    userDropdown: document.getElementById('userDropdown'),
    userMenuChangePassword: document.getElementById('userMenuChangePassword'),
    userMenuLogout: document.getElementById('userMenuLogout'),
    navTabs: document.querySelectorAll('.nav-tab'),
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    fileInfo: document.getElementById('fileInfo'),
    fileName: document.getElementById('fileName'),
    uploadProgress: document.getElementById('uploadProgress'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    uploadValidation: document.getElementById('uploadValidation'),
    validationContent: document.getElementById('validationContent'),
    confirmUploadBtn: document.getElementById('confirmUploadBtn'),
    exportButtons: document.querySelectorAll('.export-btn'),
    exportBtn: document.getElementById('exportBtn'),
    exportSuccess: document.getElementById('exportSuccess'),
    exportStartDate: document.getElementById('exportStartDate'),
    exportEndDate: document.getElementById('exportEndDate'),
    serviceType: document.getElementById('serviceType'),
    exportInfo: document.getElementById('exportInfo'),
    reportFilters: document.querySelectorAll('.report-filter'),
    reportMetricCards: document.querySelectorAll('.report-card.selectable[data-metric]'),
    reportActionCards: document.querySelectorAll('.report-card.selectable[data-action]'),
    dashboardMetricCards: document.querySelectorAll('.summary-card.selectable[data-metric]'),
    dashboardActionCards: document.querySelectorAll('.summary-card.selectable[data-action]'),
    reportChartContainers: document.querySelectorAll('.chart-container[data-metric]'),
    reportAlertsSection: document.getElementById('reportAlertsSection'),
    dashboardChartTitle: document.getElementById('dashboardChartTitle'),
    dashboardTrendSection: document.getElementById('dashboardTrendSection'),
    dashboardAlertsSection: document.getElementById('dashboardAlertsSection'),
    dashboardExportSection: document.getElementById('dashboardExportSection'),
    alertsTitle: document.getElementById('alertsTitle'),
    alertItems: document.querySelectorAll('.alerts-list .alert-item'),
    currentPageTitle: document.getElementById('currentPageTitle'),
    userName: document.getElementById('userName'),
    passwordChangeModal: document.getElementById('passwordChangeModal'),
    passwordChangeForm: document.getElementById('passwordChangeForm'),
    currentPasswordInput: document.getElementById('currentPassword'),
    newPasswordInput: document.getElementById('newPassword'),
    confirmNewPasswordInput: document.getElementById('confirmNewPassword'),
    passwordChangeError: document.getElementById('passwordChangeError'),
    passwordChangeCloseBtn: document.getElementById('passwordChangeCloseBtn'),
    approvalModal: document.getElementById('approvalModal'),
    approvalPassword: document.getElementById('approvalPassword'),
    approvalCopyBtn: document.getElementById('approvalCopyBtn')
};

const chartInstances = {
    trend: null,
    week: null,
    garantias: null,
    repruebasDonut: null
};

function initApp() {
    if (!DOM.loginForm) {
        console.error('No se encontró el formulario de login');
        return;
    }

    DOM.loginForm.addEventListener('submit', handleLogin);
    if (DOM.userMenuButton) {
        DOM.userMenuButton.addEventListener('click', toggleUserMenu);
    }
    if (DOM.userMenuChangePassword) {
        DOM.userMenuChangePassword.addEventListener('click', () => {
            closeUserMenu();
            showPasswordChangeModal(false);
        });
    }
    if (DOM.userMenuLogout) {
        DOM.userMenuLogout.addEventListener('click', () => {
            closeUserMenu();
            handleLogout();
        });
    }
    document.addEventListener('click', handleDocumentClick);
    DOM.navTabs.forEach(tab => tab.addEventListener('click', () => setActiveTab(tab.dataset.tab)));
    if (DOM.passwordChangeForm) {
        DOM.passwordChangeForm.addEventListener('submit', handlePasswordChangeSubmit);
    }
    if (DOM.passwordChangeCloseBtn) {
        DOM.passwordChangeCloseBtn.addEventListener('click', handlePasswordChangeSkip);
    }

    if (DOM.approvalCopyBtn) {
        DOM.approvalCopyBtn.addEventListener('click', copyApprovalPassword);
    }

    DOM.dropZone.addEventListener('click', () => DOM.fileInput.click());
    DOM.dropZone.addEventListener('dragover', onDropZoneDragOver);
    DOM.dropZone.addEventListener('dragleave', onDropZoneDragLeave);
    DOM.dropZone.addEventListener('drop', onDropZoneDrop);

    DOM.fileInput.addEventListener('change', onFileInputChange);
    DOM.confirmUploadBtn.addEventListener('click', onConfirmUpload);

    const removeFileBtn = document.getElementById('removeFileBtn');
    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', resetUpload);
    }
    DOM.exportButtons.forEach(btn => btn.addEventListener('click', onExportFormatChange));
    DOM.exportBtn.addEventListener('click', onExport);
    DOM.exportStartDate.addEventListener('change', updateExportInfo);
    DOM.exportEndDate.addEventListener('change', updateExportInfo);
    DOM.serviceType.addEventListener('change', updateExportInfo);
        
    DOM.reportMetricCards.forEach(card => card.addEventListener('click', () => setActiveMetric(card.dataset.metric)));
    DOM.reportActionCards.forEach(card => card.addEventListener('click', () => setReportView(card.dataset.action)));
    DOM.dashboardMetricCards.forEach(card => card.addEventListener('click', () => setActiveMetric(card.dataset.metric)));
    DOM.dashboardActionCards.forEach(card => card.addEventListener('click', () => handleDashboardAction(card.dataset.action)));
    setActiveMetric(appState.activeMetric);
    setDashboardView('metric');
    setReportView('metric');
    updateExportInfo();
}

function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!email || !password) {
        showLoginError('Ingresa email y contraseña');
        return;
    }

    // Mostrar loading
    const loginBtn = event.target.querySelector('button[type="submit"]');
    const originalText = loginBtn.textContent;
    loginBtn.textContent = 'Cargando...';
    loginBtn.disabled = true;

    // Hacer petición al API
    fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || 'Error en login');
            });
        }
        return response.json();
    })
    .then(data => {
        // Asignar token y datos del usuario primero
        appState.token = data.access_token;
        appState.user = data.nombre;
        appState.rol = data.rol;
        appState.isLoggedIn = true;

        // Guardar en localStorage
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('userName', data.nombre);
        localStorage.setItem('userRole', data.rol);
        localStorage.setItem('userId', data.usuario_id);

        // Mostrar la app
        DOM.loginScreen.classList.remove('active');
        DOM.appScreen.classList.add('active');
        DOM.userName.textContent = data.nombre;

        // Guardar si el usuario debe cambiar contraseña
        appState.mustChangePassword = data.debe_cambiar_password;
        localStorage.setItem('mustChangePassword', data.debe_cambiar_password ? 'true' : 'false');

        updateNavigation();

        if (data.debe_cambiar_password) {
            showPasswordChangeModal(true);
        } else {
            // Cargar datos reales (al final, después de asignar token)
            loadDashboardData().then(() => initCharts());
        }

        // Limpiar formulario
        DOM.loginForm.reset();
        clearLoginError();
    })
    .catch(error => {
        console.error('Error en login:', error);
        showLoginError(error.message || 'Error al iniciar sesión');
    })
    .finally(() => {
        loginBtn.textContent = originalText;
        loginBtn.disabled = false;
    });
}

function showPasswordChangeModal(required = false) {
    appState.passwordChangeModalRequired = required;
    if (DOM.passwordChangeModal) {
        DOM.passwordChangeModal.classList.add('active');
    }
}

function hidePasswordChangeModal() {
    if (DOM.passwordChangeModal) {
        DOM.passwordChangeModal.classList.remove('active');
    }
}

function showApprovalModal(password) {
    if (DOM.approvalPassword) {
        DOM.approvalPassword.textContent = password;
    }
    if (DOM.approvalModal) {
        DOM.approvalModal.classList.add('active');
    }
}

function hideApprovalModal() {
    if (DOM.approvalModal) {
        DOM.approvalModal.classList.remove('active');
    }
}

function toggleUserMenu(event) {
    event.stopPropagation();
    if (!DOM.userDropdown) return;
    DOM.userDropdown.classList.toggle('active');
}

function closeUserMenu() {
    if (DOM.userDropdown) {
        DOM.userDropdown.classList.remove('active');
    }
}

function handleDocumentClick(event) {
    if (!DOM.userDropdown || !DOM.userMenuButton) return;

    const target = event.target;
    if (DOM.userDropdown.contains(target) || DOM.userMenuButton.contains(target)) {
        return;
    }

    closeUserMenu();
}

function handlePasswordChangeSkip() {
    hidePasswordChangeModal();
    if (appState.passwordChangeModalRequired) {
        handleLogout();
    }
}

function copyApprovalPassword() {
    if (!DOM.approvalPassword) return;
    const password = DOM.approvalPassword.textContent;
    if (!password) return;

    navigator.clipboard.writeText(password)
        .then(() => {
            alert('Contraseña temporal copiada al portapapeles');
        })
        .catch(() => {
            alert('No se pudo copiar la contraseña. Por favor copia manualmente.');
        });
}

function showPasswordChangeError(message) {
    if (DOM.passwordChangeError) {
        DOM.passwordChangeError.textContent = message;
        DOM.passwordChangeError.style.display = 'block';
    }
}

function clearPasswordChangeError() {
    if (DOM.passwordChangeError) {
        DOM.passwordChangeError.textContent = '';
        DOM.passwordChangeError.style.display = 'none';
    }
}

async function handlePasswordChangeSubmit(event) {
    event.preventDefault();

    clearPasswordChangeError();

    const currentPassword = DOM.currentPasswordInput.value.trim();
    const newPassword = DOM.newPasswordInput.value.trim();
    const confirmPassword = DOM.confirmNewPasswordInput.value.trim();

    if (!currentPassword || !newPassword || !confirmPassword) {
        showPasswordChangeError('Completa todos los campos');
        return;
    }

    if (newPassword !== confirmPassword) {
        showPasswordChangeError('Las nuevas contraseñas no coinciden');
        return;
    }

    try {
        await fetchWithAuth(`${API_BASE_URL}/usuarios/me/cambiar-password`, {
            method: 'PUT',
            body: JSON.stringify({
                password_actual: currentPassword,
                password_nuevo: newPassword
            })
        });

        appState.mustChangePassword = false;
        localStorage.setItem('mustChangePassword', 'false');
        hidePasswordChangeModal();
        loadDashboardData().then(() => initCharts());
        DOM.passwordChangeForm.reset();
    } catch (error) {
        showPasswordChangeError(error.message || 'Error al cambiar contraseña');
    }
}

function showLoginError(message) {
    let errorDiv = document.getElementById('loginErrorMessage');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'loginErrorMessage';
        errorDiv.style.cssText = 'color: #e74c3c; background: #fadbd8; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 14px;';
        DOM.loginForm.insertBefore(errorDiv, DOM.loginForm.firstChild);
    }
    errorDiv.textContent = `❌ ${message}`;
    errorDiv.style.display = 'block';
}

function clearLoginError() {
    const errorDiv = document.getElementById('loginErrorMessage');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

function handleLogout() {
    // Limpiar localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('userName');
    localStorage.removeItem('userRole');
    localStorage.removeItem('userId');
    localStorage.removeItem('mustChangePassword');

    // Resetear estado
    appState.isLoggedIn = false;
    appState.token = null;
    appState.user = null;
    appState.rol = null;
    appState.mustChangePassword = false;
    closeUserMenu();

    // Volver al login
    DOM.appScreen.classList.remove('active');
    DOM.loginScreen.classList.add('active');
    clearLoginError();
}

function setActiveTab(tabName) {
    const titles = {
        dashboard: 'Dashboard',
        carga: 'Módulo Analista',
        garantias: 'Módulo Garantías',
        exportes: 'Módulo de Exportes',
        reportes: 'Módulo de Reportes',
        usuarios: 'Gestión de Usuarios'
    };

    DOM.navTabs.forEach(tab => tab.classList.toggle('active', tab.dataset.tab === tabName));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    const selectedTab = document.getElementById(`${tabName}Tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    DOM.currentPageTitle.textContent = titles[tabName] || '';

    if (tabName === 'carga' && isAnalistaRole()) {
        loadAnalistaModuleData();
    }

    if (tabName === 'garantias' && isGarantiasRole()) {
        loadGarantiasModuleData();
    }

    if (tabName === 'reportes') {
        loadReportesData('semana');
    }
}

function onDropZoneDragOver(event) {
    event.preventDefault();
    DOM.dropZone.classList.add('dragover');
}

function onDropZoneDragLeave() {
    DOM.dropZone.classList.remove('dragover');
}

function onDropZoneDrop(event) {
    event.preventDefault();
    DOM.dropZone.classList.remove('dragover');

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

function onFileInputChange(event) {
    const file = event.target.files[0];
    if (file) {
        handleFileSelect(file);
    }
}

function handleFileSelect(file) {
    const validation = validateFile(file);
    if (!validation.valid) {
        showUploadError(validation.message);
        return;
    }

    appState.uploadedFile = file;
    DOM.fileInfo.style.display = 'flex';
    DOM.fileName.textContent = `📄 ${file.name}`;
    DOM.uploadValidation.style.display = 'none';
    DOM.confirmUploadBtn.style.display = 'none';

    simulateUpload();
}

function validateFile(file) {
    const extension = file.name.split('.').pop()?.toLowerCase();
    const allowedExtensions = ['csv', 'xlsx', 'xls'];
    const typeValid = FILE_CONFIG.allowedTypes.includes(file.type) || allowedExtensions.includes(extension);

    if (!typeValid) {
        return {
            valid: false,
            message: `Formato no permitido: ${file.type || extension || 'desconocido'}`
        };
    }

    if (file.size > FILE_CONFIG.maxSize) {
        return {
            valid: false,
            message: 'El archivo supera el tamaño máximo permitido de 10 MB'
        };
    }

    return { valid: true };
}

function showUploadError(message) {
    DOM.validationContent.textContent = '';
    DOM.validationContent.appendChild(createValidationMessage(message, 'validation-error'));
    DOM.uploadValidation.style.display = 'block';
    DOM.confirmUploadBtn.style.display = 'none';
    DOM.uploadProgress.style.display = 'none';
}

function simulateUpload() {
    DOM.uploadProgress.style.display = 'block';
    let progress = 0;

    const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            showValidation();
        }

        setUploadProgress(progress);
    }, 300);
}

function setUploadProgress(percentage) {
    DOM.progressFill.style.width = `${Math.round(percentage)}%`;
    DOM.progressText.textContent = `${Math.round(percentage)}%`;
}

function showValidation() {
    DOM.validationContent.textContent = '';
    
    const fileName = appState.uploadedFile ? appState.uploadedFile.name : 'archivo';
    const fileSize = appState.uploadedFile ? (appState.uploadedFile.size / 1024).toFixed(1) + ' KB' : '';
    
    DOM.validationContent.appendChild(
        createValidationMessage(`✅ Archivo listo para cargar: ${fileName} (${fileSize})`, 'validation-success')
    );
    DOM.validationContent.appendChild(
        createValidationMessage('ℹ Haz clic en "CONFIRMAR CARGA" para procesar el archivo', 'validation-success')
    );

    DOM.uploadValidation.style.display = 'block';
    DOM.confirmUploadBtn.style.display = 'block';
}

function createValidationMessage(text, className) {
    const message = document.createElement('div');
    message.className = className;
    message.textContent = text;
    return message;
}

async function onConfirmUpload() {
    if (!appState.uploadedFile) {
        showUploadError('No hay archivo seleccionado');
        return;
    }

    DOM.confirmUploadBtn.disabled = true;
    DOM.confirmUploadBtn.textContent = 'Cargando...';

    try {
        const formData = new FormData();
        formData.append('file', appState.uploadedFile);

        const response = await fetch(`${API_BASE_URL}/repruebas/carga`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${appState.token}`
            },
            body: formData
        });

        if (response.status === 401) {
            handleLogout();
            throw new Error('Token expirado. Por favor, inicia sesión nuevamente.');
        }

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Error al cargar el archivo');
        }

        const result = await response.json();
        appState.uploadCompleted = true;

        DOM.validationContent.appendChild(
            createValidationMessage(
                `✅ ${result.mensaje} · ${result.registros_insertados} registros insertados`,
                'validation-success'
            )
        );

        if (isAnalistaRole()) {
            updateAnalistaVisibility();
            await loadAnalistaResumen();
            await loadAnalistaModuleData();
        }

        alert(`Archivo cargado exitosamente (${result.registros_insertados} registros)`);
        loadDashboardData();
    } catch (error) {
        showUploadError(error.message || 'Error al cargar el archivo');
    } finally {
        DOM.confirmUploadBtn.disabled = false;
        DOM.confirmUploadBtn.textContent = 'CONFIRMAR CARGA';
    }
}

function resetUpload() {
    DOM.fileInfo.style.display = 'none';
    DOM.uploadProgress.style.display = 'none';
    DOM.uploadValidation.style.display = 'none';
    DOM.confirmUploadBtn.style.display = 'none';
    DOM.progressFill.style.width = '0%';
    appState.uploadedFile = null;
    DOM.fileInput.value = '';
}

function onExportFormatChange(event) {
    const selectedButton = event.currentTarget;
    DOM.exportButtons.forEach(button =>
        button.classList.toggle('active', button === selectedButton)
    );
    appState.exportFormat = selectedButton.dataset.format;
    
    const fechasSection = document.getElementById('exportFechasSection');
    if (fechasSection) {
        fechasSection.style.display = selectedButton.dataset.format === 'fallas-masivas' ? 'none' : 'block';
    }
}


function onExport() {
    ejecutarExporte();
}

async function ejecutarExporte() {
    const formato = document.querySelector('.export-btn.active')?.dataset.format;
    const fechaInicio = document.getElementById('exportStartDate').value;
    const fechaFin = document.getElementById('exportEndDate').value;
    const errorDiv = document.getElementById('exportError');
    const successDiv = document.getElementById('exportSuccess');

    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';

    if (!formato) {
        errorDiv.textContent = '❌ Selecciona un tipo de exportación';
        errorDiv.style.display = 'block';
        return;
    }

    const exportBtn = document.getElementById('exportBtn');
    exportBtn.textContent = '⏳ Generando...';
    exportBtn.disabled = true;

    try {
        let url = `${API_BASE_URL}/exportes/${formato}`;
        
        if (formato !== 'fallas-masivas') {
            const params = new URLSearchParams();
            if (fechaInicio) params.append('fecha_inicio', fechaInicio);
            if (fechaFin) params.append('fecha_fin', fechaFin);
            url += `?${params.toString()}`;
        }

        const response = await fetch(url, {
            headers: { Authorization: `Bearer ${appState.token}` }
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Error al exportar');
        }

        const blob = await response.blob();
        const nombreArchivo = {
            'repruebas': 'repruebas.xlsx',
            'fallas-masivas': 'fallas_masivas.xlsx',
            'garantias': 'garantias.xlsx'
        }[formato] || 'exportacion.xlsx';

        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = nombreArchivo;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(link.href), 1000);

        successDiv.style.display = 'block';
        setTimeout(() => successDiv.style.display = 'none', 4000);

    } catch (error) {
        errorDiv.textContent = `❌ ${error.message}`;
        errorDiv.style.display = 'block';
    } finally {
        exportBtn.textContent = '📥 EXPORTAR EXCEL';
        exportBtn.disabled = false;
    }

}

function updateExportInfo() {
    const start = DOM.exportStartDate.value;
    const end = DOM.exportEndDate.value;
    const service = DOM.serviceType.value;
    const metricLabel = appState.activeMetric === 'garantias' ? 'Garantías' : 'Repruebas';

    DOM.exportInfo.textContent = `Se exportarán ${document.getElementById('exportesCount').textContent} registros de ${metricLabel} para ${service} entre ${start} y ${end}`;
}

function setReportView(view) {
    DOM.reportChartContainers.forEach(container => {
        container.style.display = view === 'metric' && container.dataset.metric === appState.activeMetric ? 'block' : 'none';
    });

    if (DOM.reportAlertsSection) {
        DOM.reportAlertsSection.style.display = view === 'alerts' ? 'block' : 'none';
    }

    DOM.reportMetricCards.forEach(card =>
        card.classList.toggle('active', card.dataset.metric === appState.activeMetric && view === 'metric')
    );

    DOM.reportActionCards.forEach(card =>
        card.classList.toggle('active', view === 'alerts' && card.dataset.action === 'alerts')
    );
}

function setDashboardView(view) {
    DOM.dashboardTrendSection.style.display = view === 'metric' ? 'block' : 'none';
    DOM.dashboardAlertsSection.style.display = view === 'alerts' ? 'block' : 'none';
    DOM.dashboardExportSection.style.display = view === 'exportes' ? 'block' : 'none';

    if (view === 'metric') {
        DOM.dashboardChartTitle.textContent = METRIC_DATA[appState.activeMetric]?.dashboardChartTitle || 'Tendencia mensual';
        updateDashboardChart(appState.activeMetric);
    }
}

function handleDashboardAction(action) {
    if (action === 'exportes') {
        setDashboardView('exportes');
        updateExportInfo();
        return;
    }

    if (action === 'alerts') {
        setDashboardView('alerts');
        return;
    }
}

function onReportFilterChange(event) {
    console.log('onReportFilterChange llamado', event.currentTarget.dataset.period);
    const selectedButton = event.currentTarget;
    DOM.reportFilters.forEach(button =>
        button.classList.toggle('active', button === selectedButton)
    );
    const periodo = selectedButton.dataset.period;
    loadReportesData(periodo);
}

async function loadReportesData(periodo = 'semana') {
    try {
        const data = await fetchWithAuth(`${API_BASE_URL}/danos/dashboard/reportes?periodo=${periodo}`);

        // Actualizar tarjetas
        document.querySelector('.report-card[data-metric="repruebas"] .report-number').textContent = data.total_repruebas || 0;
        document.querySelector('.report-card[data-metric="garantias"] .report-number').textContent = data.total_garantias || 0;
        document.querySelector('.report-card[data-action="alerts"] .report-number').textContent = data.total_fallas || 0;

        // Actualizar gráfica
        const ctx = document.getElementById('weekChart');
        if (ctx) {
            if (chartInstances.week) chartInstances.week.destroy();
            chartInstances.week = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.grafica.map(r => r.etiqueta),
                    datasets: [{
                        label: 'Repruebas',
                        data: data.grafica.map(r => r.cantidad),
                        backgroundColor: '#00a8e8',
                        borderRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } }
                }
            });
        }
    } catch (error) {
        console.error('Error cargando reportes:', error);
    }
}

function setActiveMetric(metric) {
    appState.activeMetric = metric;

    DOM.reportMetricCards.forEach(card =>
        card.classList.toggle('active', card.dataset.metric === metric)
    );

    DOM.dashboardMetricCards.forEach(card =>
        card.classList.toggle('active', card.dataset.metric === metric)
    );

    DOM.reportChartContainers.forEach(container =>
        container.style.display = container.dataset.metric === metric ? 'block' : 'none'
    );

    DOM.alertItems.forEach(item =>
        item.style.display = item.dataset.metric === metric ? 'block' : 'none'
    );

    if (DOM.alertsTitle) {
        DOM.alertsTitle.textContent = METRIC_DATA[metric]?.alertTitle || '🚨 Alertas de fallas masivas';
    }

    if (DOM.dashboardChartTitle) {
        DOM.dashboardChartTitle.textContent = METRIC_DATA[metric]?.dashboardChartTitle || 'Tendencia mensual';
    }

    setDashboardView('metric');
    updateDashboardChart(metric);
}

function updateDashboardChart(metric) {
    if (!chartInstances.trend) {
        return;
    }

    const metricData = METRIC_DATA[metric] || METRIC_DATA.repruebas;
    chartInstances.trend.data.datasets[0].label = metricData.dashboardTrendLabel;
    chartInstances.trend.data.datasets[0].data = metricData.dashboardTrend;
    chartInstances.trend.update();
}

function initCharts() {
    destroyCharts();

    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
        // Gráfica de dona - estados de repruebas
        if (chartInstances.trend) chartInstances.trend.destroy();
        
        const estados = appState.repruebasEstado || [];
        const colores = {
            'OK': '#27ae60',
            'Sin reprueba': '#95a5a6',
            'Falla física': '#f39c12',
            'Falla lógica': '#f1c40f',
            'Falla física lógica': '#e74c3c'
        };

        chartInstances.trend = new Chart(trendCtx, {
            type: 'doughnut',
            data: {
                labels: estados.map(e => e.estado),
                datasets: [{
                    data: estados.map(e => e.cantidad),
                    backgroundColor: estados.map(e => colores[e.estado] || '#003d82'),
                    borderColor: 'white',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: 'Repruebas por estado' }
                }
            }
        });
    }

    const weekCtx = document.getElementById('weekChart');
    if (weekCtx) {
        chartInstances.week = new Chart(weekCtx, {
            type: 'bar',
            data: {
                labels: ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7'],
                datasets: [{
                    label: 'Repruebas',
                    data: [15, 22, 18, 25, 20, 28, 14],
                    backgroundColor: '#00a8e8',
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    const garantiasCtx = document.getElementById('garantiasChart');
    if (garantiasCtx) {
        chartInstances.garantias = new Chart(garantiasCtx, {
            type: 'doughnut',
            data: {
                labels: ['Activas (65%)', 'Pendientes (22%)', 'Cerradas (13%)'],
                datasets: [{
                    data: [65, 22, 13],
                    backgroundColor: ['#00a8e8', '#f39c12', '#95a5a6'],
                    borderColor: 'white',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    const alertCtx = document.getElementById('alertChart');
    if (alertCtx) {
        chartInstances.alert = new Chart(alertCtx, {
            type: 'bar',
            data: {
                labels: ['Críticas', 'Moderadas', 'Bajas'],
                datasets: [{
                    label: 'Alertas',
                    data: [12, 7, 3],
                    backgroundColor: ['#e74c3c', '#f39c12', '#00a8e8'],
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    const exportCtx = document.getElementById('exportChart');
    if (exportCtx) {
        chartInstances.export = new Chart(exportCtx, {
            type: 'line',
            data: {
                labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                datasets: [{
                    label: 'Exportes',
                    data: [8, 10, 9, 12, 14, 15],
                    backgroundColor: 'rgba(0, 168, 232, 0.2)',
                    borderColor: '#00a8e8',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
}

function destroyCharts() {
    Object.values(chartInstances).forEach(chart => {
        if (chart) {
            chart.destroy();
        }
    });

    chartInstances.trend = null;
    chartInstances.week = null;
    chartInstances.garantias = null;
    chartInstances.repruebasDonut = null;
}

window.addEventListener('load', () => {
    // Verificar si ya hay sesión activa
    if (appState.isLoggedIn && appState.token) {
        DOM.userName.textContent = localStorage.getItem('userName') || 'Usuario';
        DOM.loginScreen.classList.remove('active');
        DOM.appScreen.classList.add('active');
        updateNavigation();
        if (appState.mustChangePassword) {
            showPasswordChangeModal();
        } else {
            loadDashboardData().then(() => initCharts());
        }
    }
    initApp();
});

// ==================== USUARIOS Y SOLICITUDES ====================

function openAccessRequestModal(event) {
    if (event) event.preventDefault();
    document.getElementById('accessRequestModal').style.display = 'flex';
}

function closeAccessRequestModal() {
    document.getElementById('accessRequestModal').style.display = 'none';
    document.getElementById('accessRequestForm').reset();
}

async function submitAccessRequest(event) {
    event.preventDefault();

    const data = {
        nombre: document.getElementById('accessName').value,
        email: document.getElementById('accessEmail').value,
        zona: document.getElementById('accessZona').value,
        rol_solicitado: document.getElementById('accessRol').value,
        motivo: document.getElementById('accessMotivo').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/solicitudes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al enviar solicitud');
        }

        alert('✅ Solicitud enviada. Te contactaremos pronto.');
        closeAccessRequestModal();
    } catch (error) {
        alert(`❌ ${error.message}`);
    }
}

function openNewUserModal() {
    document.getElementById('newUserModal').style.display = 'flex';
}

function closeNewUserModal() {
    document.getElementById('newUserModal').style.display = 'none';
    document.getElementById('newUserForm').reset();
}
async function submitNewUser(event) {
    event.preventDefault();

    const data = {
        nombre: document.getElementById('newUserName').value,
        email: document.getElementById('newUserEmail').value,
        rol: document.getElementById('newUserRol').value,
        zona: document.getElementById('newUserZona').value
    };

    try {
        const result = await fetchWithAuth(`${API_BASE_URL}/usuarios`, {
            method: 'POST',
            body: JSON.stringify(data)
        });

        closeNewUserModal();
        loadUsers();
        
        if (result.contraseña_temporal) {
            showApprovalModal(result.contraseña_temporal);
        } else {
            alert(`✅ Usuario creado exitosamente.`);
        }
    } catch (error) {
        alert(`❌ ${error.message}`);
    }
}
async function loadUsers() {
    const container = document.getElementById('usuariosContainer');
    
    try {
        const users = await fetchWithAuth(`${API_BASE_URL}/usuarios`);
        
        if (users.length === 0) {
            container.innerHTML = '<p>No hay usuarios registrados</p>';
            return;
        }

        let html = '<div class="usuarios-table">';
        users.forEach(user => {
            const status = user.activo ? '✅ Activo' : '❌ Inactivo';
            html += `
                <div class="usuario-row">
                    <div class="usuario-info">
                        <strong>${user.nombre}</strong>
                        <p>${user.email}</p>
                        <p>Rol: ${user.rol} | Zona: ${user.zona}</p>
                    </div>
                    <div class="usuario-status">${status}</div>
                    <div class="usuario-actions">
                        ${user.activo ? `<button class="btn-small btn-danger" onclick="desactivateUser(${user.id})">Desactivar</button>` : ''}
                    </div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<p>❌ ${error.message}</p>`;
    }
}

async function desactivateUser(userId) {
    if (!confirm('¿Desactivar este usuario?')) return;

    try {
        await fetchWithAuth(`${API_BASE_URL}/usuarios/${userId}`, {
            method: 'DELETE'
        });

        alert('✅ Usuario desactivado');
        loadUsers();
    } catch (error) {
        alert(`❌ ${error.message}`);
    }
}

async function loadUserRequests() {
    const container = document.getElementById('solicitudesList');
    const section = document.getElementById('solicitudesContainer');

    try {
        const solicitudes = await fetchWithAuth(`${API_BASE_URL}/solicitudes?estado=pendiente`);
        
        if (solicitudes.length === 0) {
            container.innerHTML = '<p>No hay solicitudes pendientes</p>';
        } else {
            let html = '';
            solicitudes.forEach(sol => {
                html += `
                    <div class="solicitud-card">
                        <div class="solicitud-info">
                            <strong>${sol.nombre}</strong>
                            <p>Email: ${sol.email}</p>
                            <p>Rol solicitado: ${sol.rol_solicitado} | Zona: ${sol.zona}</p>
                            <p>Motivo: ${sol.motivo}</p>
                        </div>
                        <div class="solicitud-actions">
                            <button class="btn-success" onclick="approveSolicitud(${sol.id})">✅ Aprobar</button>
                            <button class="btn-danger" onclick="rejectSolicitud(${sol.id})">❌ Rechazar</button>
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        section.style.display = 'block';
        document.getElementById('usuariosContainer').style.display = 'none';
    } catch (error) {
        alert(`❌ ${error.message}`);
    }
}

async function approveSolicitud(solicitudId) {
    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/solicitudes/${solicitudId}/aprobar`, {
            method: 'PUT'
        });

        if (response.contraseña_temporal) {
            showApprovalModal(response.contraseña_temporal);
        } else {
            alert('✅ Solicitud aprobada');
        }

        loadUserRequests();
    } catch (error) {
        alert(`❌ ${error.message}`);
    }
}

async function rejectSolicitud(solicitudId) {
    if (!confirm('¿Rechazar esta solicitud?')) return;

    try {
        await fetchWithAuth(`${API_BASE_URL}/solicitudes/${solicitudId}/rechazar`, {
            method: 'PUT'
        });

        alert('✅ Solicitud rechazada');
        loadUserRequests();
    } catch (error) {
        alert(`❌ ${error.message}`);
    }
}

async function fetchWithAuth(url, options = {}) {
    // Función helper para hacer fetch con token de autorización
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (appState.token) {
        headers['Authorization'] = `Bearer ${appState.token}`;
    }

    // Debug temporal
    console.log('Token en appState:', appState.token);
    console.log('Headers que se envían:', headers);

    const response = await fetch(url, {
        ...options,
        headers
    });

    // Si recibimos 401, el token es inválido o expiró
    if (response.status === 401) {
        handleLogout();
        throw new Error('Token expirado. Por favor, inicia sesión nuevamente.');
    }

    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error en la petición');
    }

    return response.json();
}

function isAnalistaRole() {
    return appState.rol === 'analista' || appState.rol === 'supervisor';
}

function isGarantiasRole() {
    return appState.rol === 'garantias' || appState.rol === 'supervisor';
}

function updateAnalistaVisibility() {
    const chartsSection = document.getElementById('analistaChartsSection');
    const fallasSection = document.getElementById('analistaFallasSection');
    const historialSection = document.getElementById('analistaHistorialSection');
    const showRoleSections = isAnalistaRole();

    if (chartsSection) {
        chartsSection.style.display = showRoleSections && appState.uploadCompleted ? 'block' : 'none';
    }
    if (fallasSection) {
        fallasSection.style.display = showRoleSections ? 'block' : 'none';
    }
    if (historialSection) {
        historialSection.style.display = showRoleSections ? 'block' : 'none';
    }
}

async function loadAnalistaModuleData() {
    if (!isAnalistaRole()) {
        return;
    }

    updateAnalistaVisibility();
    initCargaDatosMaestros();

    await Promise.all([
        loadReppuebasMap(),
        loadFallasMasivas(),
        loadGestionesHistorial()
    ]);

    if (appState.uploadCompleted) {
        await loadAnalistaResumen();
    }
}

async function loadReppuebasMap() {
    try {
        const repruebas = await fetchWithAuth(`${API_BASE_URL}/repruebas`);
        const map = {};
        repruebas.forEach(r => {
            if (r.pedido_id) {
                map[r.pedido_id] = r.codigo_estado || 'Sin reprueba';
            }
        });
        appState.repruebasMap = map;
    } catch (error) {
        console.error('Error cargando repruebas:', error);
        appState.repruebasMap = {};
    }
}

async function loadAnalistaResumen() {
    const cardsContainer = document.getElementById('repruebasSummaryCards');
    if (!cardsContainer) {
        return;
    }

    try {
        const data = await fetchWithAuth(`${API_BASE_URL}/analista/resumen-repruebas`);
        const conteos = {};
        ANALISTA_ESTADOS.forEach(estado => {
            conteos[estado] = 0;
        });

        data.resumen.forEach(item => {
            conteos[item.estado] = item.cantidad;
        });

        cardsContainer.innerHTML = ANALISTA_ESTADOS.map(estado => `
            <div class="analista-summary-card" style="border-top-color: ${ANALISTA_COLORES[estado]}">
                <span class="count">${conteos[estado] || 0}</span>
                <span class="label">${estado}</span>
            </div>
        `).join('');

        renderRepruebasDonutChart(ANALISTA_ESTADOS.map(estado => conteos[estado] || 0));
    } catch (error) {
        cardsContainer.innerHTML = `<p class="analista-empty">❌ ${error.message}</p>`;
        console.error('Error cargando resumen:', error);
    }
}

function renderRepruebasDonutChart(values) {
    const canvas = document.getElementById('repruebasDonutChart');
    if (!canvas) {
        return;
    }

    if (chartInstances.repruebasDonut) {
        chartInstances.repruebasDonut.destroy();
    }

    chartInstances.repruebasDonut = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ANALISTA_ESTADOS,
            datasets: [{
                data: values,
                backgroundColor: ANALISTA_ESTADOS.map(estado => ANALISTA_COLORES[estado]),
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

async function loadFallasMasivas() {
    const container = document.getElementById('fallasMasivasContainer');
    if (!container || !isAnalistaRole()) {
        return;
    }

    container.innerHTML = '<p class="analista-empty">Cargando fallas masivas...</p>';

    try {
        const [fallas, gestiones] = await Promise.all([
            fetchWithAuth(`${API_BASE_URL}/analista/fallas-masivas`),
            fetchWithAuth(`${API_BASE_URL}/analista/gestiones`)
        ]);

        appState.fallasMasivas = fallas;
        appState.gestionesMap = {};
        gestiones.forEach(g => {
            appState.gestionesMap[`${g.elemento_red}-${g.valor_elemento}`] = g;
        });

        if (fallas.length === 0) {
            container.innerHTML = '<p class="analista-empty">No se detectaron fallas masivas (mínimo 3 pedidos por elemento).</p>';
            return;
        }

        let html = `
            <table class="analista-data-table">
                <thead>
                    <tr>
                        <th>Elemento de red</th>
                        <th>Valor</th>
                        <th>Pedidos afectados</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
        `;

        fallas.forEach((falla, index) => {
            const key = `${falla.elemento_red}-${falla.valor_elemento}`;
            const gestion = appState.gestionesMap[key];
            const estado = gestion ? gestion.estado : 'no_gestionado';
            const estadoLabel = ESTADO_GESTION_LABELS[estado] || estado;

            html += `
                <tr>
                    <td>${ELEMENTO_LABELS[falla.elemento_red] || falla.elemento_red}</td>
                    <td>${falla.valor_elemento}</td>
                    <td>${falla.total_pedidos}</td>
                    <td><span class="estado-badge estado-${estado}">${estadoLabel}</span></td>
                    <td>
                        <button class="btn-small btn-secondary" type="button" onclick="openGestionFallaModal(${index})">
                            Ver detalle y gestionar
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<p class="analista-empty">❌ ${error.message}</p>`;
    }
}

async function loadGestionesHistorial() {
    const container = document.getElementById('gestionesHistorialContainer');
    if (!container || !isAnalistaRole()) {
        return;
    }

    container.innerHTML = '<p class="analista-empty">Cargando historial...</p>';

    try {
        const gestiones = await fetchWithAuth(`${API_BASE_URL}/analista/gestiones`);

        if (gestiones.length === 0) {
            container.innerHTML = '<p class="analista-empty">No hay gestiones registradas aún.</p>';
            return;
        }

        let html = `
            <table class="analista-data-table">
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Elemento</th>
                        <th>Valor</th>
                        <th>Estado</th>
                        <th>Ticket</th>
                    </tr>
                </thead>
                <tbody>
        `;

        gestiones.forEach(g => {
            const fecha = g.fecha_gestion || g.fecha_deteccion;
            const fechaStr = fecha ? new Date(fecha).toLocaleDateString('es-CO') : '-';
            const elemento = `${ELEMENTO_LABELS[g.elemento_red] || g.elemento_red}`;
            const estadoLabel = ESTADO_GESTION_LABELS[g.estado] || g.estado;

            html += `
                <tr>
                    <td>${fechaStr}</td>
                    <td>${elemento}</td>
                    <td>${g.valor_elemento}</td>
                    <td><span class="estado-badge estado-${g.estado}">${estadoLabel}</span></td>
                    <td>${g.numero_ticket || '—'}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<p class="analista-empty">❌ ${error.message}</p>`;
    }
}

function openGestionFallaModal(index) {
    const falla = appState.fallasMasivas[index];
    if (!falla) {
        return;
    }

    const key = `${falla.elemento_red}-${falla.valor_elemento}`;
    const gestionExistente = appState.gestionesMap[key];

    appState.gestionModalData = {
        falla,
        id_gestion: gestionExistente ? gestionExistente.id : null
    };

    const infoEl = document.getElementById('gestionFallaInfo');
    infoEl.innerHTML = `
        <p><strong>Elemento de red:</strong> ${ELEMENTO_LABELS[falla.elemento_red] || falla.elemento_red}</p>
        <p><strong>Valor:</strong> ${falla.valor_elemento}</p>
        <p><strong>Total pedidos afectados:</strong> ${falla.total_pedidos}</p>
    `;

    const pedidosList = document.getElementById('gestionPedidosList');
    pedidosList.innerHTML = falla.pedido_ids.map(pedidoId => {
        const tipoFalla = appState.repruebasMap[pedidoId] || 'Sin reprueba';
        return `
            <div class="gestion-pedido-item">
                <span>Pedido #${pedidoId}</span>
                <span>${tipoFalla}</span>
            </div>
        `;
    }).join('');

    document.getElementById('gestionObservaciones').value = gestionExistente?.observaciones || '';
    const estadoSelect = document.getElementById('gestionEstado');
    estadoSelect.value = gestionExistente?.estado || 'no_gestionado';
    onGestionEstadoChange();

    const modal = document.getElementById('gestionFallaModal');
    modal.classList.add('active');
}

function closeGestionFallaModal() {
    const modal = document.getElementById('gestionFallaModal');
    modal.classList.remove('active');
    appState.gestionModalData = null;
    document.getElementById('gestionFallaForm').reset();
    document.getElementById('gestionEscaladoMsg').style.display = 'none';
}

function onGestionEstadoChange() {
    const estado = document.getElementById('gestionEstado').value;
    const msg = document.getElementById('gestionEscaladoMsg');
    msg.style.display = estado === 'escalado' ? 'block' : 'none';
}

async function submitGestionFalla(event) {
    event.preventDefault();

    if (!appState.gestionModalData) {
        return;
    }

    const { falla, id_gestion } = appState.gestionModalData;
    const observaciones = document.getElementById('gestionObservaciones').value.trim();
    const estado = document.getElementById('gestionEstado').value;

    const payload = {
        elemento_red: falla.elemento_red,
        valor_elemento: falla.valor_elemento,
        pedidos_afectados: falla.pedido_ids,
        estado,
        observaciones: observaciones || null
    };

    if (id_gestion) {
        payload.id_gestion = id_gestion;
    }

    try {
        const result = await fetchWithAuth(`${API_BASE_URL}/analista/gestionar`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        closeGestionFallaModal();

        if (estado === 'escalado' && result.numero_ticket) {
            showAnalistaSuccessAlert(`Gestión escalada. Ticket generado: ${result.numero_ticket}`);
        } else {
            showAnalistaSuccessAlert('Gestión guardada correctamente');
        }

        await loadFallasMasivas();
        await loadGestionesHistorial();
    } catch (error) {
        alert(`❌ ${error.message}`);
    }
}

function showAnalistaSuccessAlert(message) {
    const existing = document.getElementById('analistaSuccessAlert');
    if (existing) {
        existing.remove();
    }

    const alert = document.createElement('div');
    alert.id = 'analistaSuccessAlert';
    alert.className = 'analista-alert-success';
    alert.textContent = `✅ ${message}`;

    const tab = document.getElementById('cargaTab');
    const header = tab.querySelector('.tab-header');
    header.insertAdjacentElement('afterend', alert);

    setTimeout(() => alert.remove(), 6000);
}

function isGarantiasRole() {
    return appState.rol === 'garantias' || appState.rol === 'supervisor';
}

function formatFecha(fecha) {
    if (!fecha) {
        return '—';
    }
    return new Date(fecha).toLocaleDateString('es-CO');
}

function getRepruebaEstadoClass(codigoEstado) {
    if (codigoEstado === 'Falla física') {
        return 'reprueba-estado-fisica';
    }
    if (codigoEstado === 'Falla lógica') {
        return 'reprueba-estado-logica';
    }
    if (codigoEstado === 'Falla física lógica') {
        return 'reprueba-estado-mixta';
    }
    return '';
}

async function buildGarantiaClienteMap(pendientes) {
    const map = {};

    pendientes.forEach(p => {
        map[p.pedido_id] = p.nombre_cliente || '—';
    });

    try {
        const [cerrados, clientes] = await Promise.all([
            fetchWithAuth(`${API_BASE_URL}/danos/cerrados`),
            fetchWithAuth(`${API_BASE_URL}/clientes`)
        ]);

        const clienteByCedula = {};
        clientes.forEach(c => {
            clienteByCedula[c.cedula_cliente] = c.nombre;
        });

        cerrados.forEach(d => {
            if (!map[d.pedido_id]) {
                map[d.pedido_id] = clienteByCedula[d.cedula_cliente] || '—';
            }
        });
    } catch (error) {
        console.error('Error construyendo mapa de clientes:', error);
    }

    appState.garantiaClienteMap = map;
    return map;
}

async function loadGarantiasModuleData() {
    if (!isGarantiasRole()) {
        return;
    }

    await Promise.all([
        loadGarantiasPendientes(),
        loadGarantiasHistorial(),
        loadGarantiasResumen()
    ]);
}

async function loadGarantiasPendientes() {
    const container = document.getElementById('garantiasPendientesContainer');
    if (!container || !isGarantiasRole()) {
        return;
    }

    container.innerHTML = '<p class="garantias-empty">Cargando pedidos pendientes...</p>';
    console.log('Iniciando carga garantias, rol:', appState.rol);

    try {
        const [pendientes, cerrados] = await Promise.all([
            fetchWithAuth(`${API_BASE_URL}/garantias/pendientes`),
            fetchWithAuth(`${API_BASE_URL}/danos/cerrados`)
        ]);

        appState.garantiaPendientes = pendientes;

        const fechaCierreMap = {};
        cerrados.forEach(d => {
            fechaCierreMap[d.pedido_id] = d.fecha_cierre;
        });

        await buildGarantiaClienteMap(pendientes);

        if (pendientes.length === 0) {
            container.innerHTML = '<p class="garantias-empty">No hay pedidos pendientes de gestión de garantía.</p>';
            return;
        }

        let html = `
            <table class="garantias-data-table">
                <thead>
                    <tr>
                        <th>Pedido ID</th>
                        <th>Cliente</th>
                        <th>Tipo falla daño</th>
                        <th>Estado reprueba</th>
                        <th>Ciudad</th>
                        <th>Fecha cierre</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
        `;

        pendientes.forEach((item, index) => {
            html += `
                <tr>
                    <td>${item.pedido_id}</td>
                    <td>${item.nombre_cliente || '—'}</td>
                    <td>${item.tipo_falla || '—'}</td>
                    <td>${item.codigo_estado || '—'}</td>
                    <td>${item.ciudad || '—'}</td>
                    <td>${formatFecha(fechaCierreMap[item.pedido_id])}</td>
                    <td>
                        <button class="btn-small btn-secondary" type="button" onclick="openGestionGarantiaModal(${index})">
                            Gestionar garantía
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
     } catch (error) {
        console.error('Error garantias:', error);
        container.innerHTML = `<p class="garantias-empty">❌ ${error.message}</p>`;
    }
}

async function loadGarantiasHistorial() {
    const container = document.getElementById('garantiasHistorialContainer');
    if (!container || !isGarantiasRole()) {
        return;
    }

    container.innerHTML = '<p class="garantias-empty">Cargando historial...</p>';

    try {
        const gestiones = await fetchWithAuth(`${API_BASE_URL}/garantias/gestiones`);

        if (gestiones.length === 0) {
            container.innerHTML = '<p class="garantias-empty">No hay gestiones de garantía registradas.</p>';
            return;
        }

        if (Object.keys(appState.garantiaClienteMap).length === 0) {
            await buildGarantiaClienteMap(appState.garantiaPendientes);
        }

        let html = `
            <table class="garantias-data-table">
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Pedido ID</th>
                        <th>Cliente</th>
                        <th>Estado</th>
                        <th>Ticket</th>
                    </tr>
                </thead>
                <tbody>
        `;

        gestiones.forEach(g => {
            const fecha = g.fecha_gestion || g.fecha_deteccion;
            const estadoLabel = ESTADO_GARANTIA_LABELS[g.estado] || g.estado;
            const cliente = appState.garantiaClienteMap[g.pedido_id] || '—';

            html += `
                <tr>
                    <td>${formatFecha(fecha)}</td>
                    <td>${g.pedido_id}</td>
                    <td>${cliente}</td>
                    <td><span class="estado-badge estado-${g.estado}">${estadoLabel}</span></td>
                    <td>${g.numero_ticket || '—'}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<p class="garantias-empty">❌ ${error.message}</p>`;
    }
}

async function loadGarantiasResumen() {
    if (!isGarantiasRole()) {
        return;
    }

    try {
        const [pendientes, gestiones] = await Promise.all([
            fetchWithAuth(`${API_BASE_URL}/garantias/pendientes`),
            fetchWithAuth(`${API_BASE_URL}/garantias/gestiones`)
        ]);

        const escaladas = gestiones.filter(g => g.estado === 'escalada').length;
        const noEscaladas = gestiones.filter(g => g.estado === 'no_escalada').length;

        document.getElementById('garantiasResumenPendientes').textContent = pendientes.length;
        document.getElementById('garantiasResumenEscaladas').textContent = escaladas;
        document.getElementById('garantiasResumenNoEscaladas').textContent = noEscaladas;
    } catch (error) {
        console.error('Error cargando resumen de garantías:', error);
    }
}

function openGestionGarantiaModal(index) {
    const item = appState.garantiaPendientes[index];
    if (!item) {
        return;
    }

    appState.garantiaModalData = item;

    const estadoClass = getRepruebaEstadoClass(item.codigo_estado);
    const infoEl = document.getElementById('gestionGarantiaInfo');
    infoEl.innerHTML = `
        <p><strong>Pedido ID:</strong> ${item.pedido_id}</p>
        <p><strong>Cliente:</strong> ${item.nombre_cliente || '—'}</p>
        <p><strong>Cédula:</strong> ${item.cedula_cliente || '—'}</p>
        <p><strong>Dirección:</strong> ${item.direccion || '—'}</p>
        <p><strong>Teléfono:</strong> ${item.telefono || '—'}</p>
        <p><strong>Ciudad:</strong> ${item.ciudad || '—'} · <strong>Barrio:</strong> ${item.barrio || '—'}</p>
        <p><strong>Tipo falla del daño:</strong> ${item.tipo_falla || '—'}</p>
        <p><strong>Estado de la reprueba:</strong></p>
        <span class="reprueba-estado ${estadoClass}">${item.codigo_estado || '—'}</span>
    `;

    document.getElementById('garantiaObservaciones').value = '';
    document.getElementById('garantiaEstado').value = 'no_escalada';
    onGarantiaEstadoChange();

    document.getElementById('gestionGarantiaModal').classList.add('active');
}

function closeGestionGarantiaModal() {
    document.getElementById('gestionGarantiaModal').classList.remove('active');
    appState.garantiaModalData = null;
    document.getElementById('gestionGarantiaForm').reset();
    document.getElementById('garantiaEscaladoMsg').style.display = 'none';
}

function onGarantiaEstadoChange() {
    const estado = document.getElementById('garantiaEstado').value;
    const msg = document.getElementById('garantiaEscaladoMsg');
    msg.style.display = estado === 'escalada' ? 'block' : 'none';
}

async function submitGestionGarantia(event) {
    event.preventDefault();

    if (!appState.garantiaModalData) {
        return;
    }

    const item = appState.garantiaModalData;
    const observaciones = document.getElementById('garantiaObservaciones').value.trim();
    const estado = document.getElementById('garantiaEstado').value;

    const payload = {
        pedido_id: item.pedido_id,
        id_reprueba: item.id_reprueba,
        estado,
        observaciones: observaciones || null
    };

    try {
        const result = await fetchWithAuth(`${API_BASE_URL}/garantias/gestionar`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        closeGestionGarantiaModal();

        if (estado === 'escalada' && result.numero_ticket) {
            showGarantiaSuccessAlert(`Garantía escalada. Ticket generado: ${result.numero_ticket}`);
        } else {
            showGarantiaSuccessAlert('Gestión de garantía guardada correctamente');
        }

        await loadGarantiasModuleData();
    } catch (error) {
        alert(`❌ ${error.message}`);
    }
}

function showGarantiaSuccessAlert(message) {
    const existing = document.getElementById('garantiaSuccessAlert');
    if (existing) {
        existing.remove();
    }

    const alert = document.createElement('div');
    alert.id = 'garantiaSuccessAlert';
    alert.className = 'garantias-alert-success';
    alert.textContent = `✅ ${message}`;

    const tab = document.getElementById('garantiasTab');
    const header = tab.querySelector('.tab-header');
    header.insertAdjacentElement('afterend', alert);

    setTimeout(() => alert.remove(), 6000);
}

function updateNavigation() {
    const rol = appState.rol;
    const analistaTab = document.querySelector('[data-tab="carga"]');
    const garantiasTab = document.querySelector('[data-tab="garantias"]');
    const usuariosTab = document.querySelector('[data-tab="usuarios"]');

    if (analistaTab) {
        analistaTab.setAttribute('style', (rol === 'analista' || rol === 'supervisor') ? 'display:flex' : 'display:none');
    }

    if (garantiasTab) {
        garantiasTab.setAttribute('style', (rol === 'garantias' || rol === 'supervisor') ? 'display:flex' : 'display:none');
    }

    if (usuariosTab) {
        usuariosTab.setAttribute('style', rol === 'supervisor' ? 'display:flex' : 'display:none');
    }
}

async function loadDashboardData() {
    try {
        const [resumen, repruebasEstado, garantiasMes, fallasMes, alertasData] = await Promise.all([
            fetchWithAuth(`${API_BASE_URL}/danos/dashboard/resumen`),
            fetchWithAuth(`${API_BASE_URL}/danos/dashboard/repruebas-por-estado`),
            fetchWithAuth(`${API_BASE_URL}/danos/dashboard/garantias-por-mes`),
            fetchWithAuth(`${API_BASE_URL}/danos/dashboard/fallas-por-mes`),
            fetchWithAuth(`${API_BASE_URL}/danos/dashboard/alertas-count`)
        ]);

        // Contadores
        document.getElementById('repuebasCount').textContent = resumen.total_repruebas || 0;
        document.getElementById('garantiasCount').textContent = resumen.daños_pendientes || 0;
        document.getElementById('alertasCount').textContent = alertasData.alertas || 0;

        // Rol y zona
        const rolZona = `${appState.rol || ''} · ${appState.zona || ''}`;
        document.getElementById('userRolZona').textContent = rolZona;

        const nombre = appState.user || '';
        const iniciales = nombre.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
        document.getElementById('userAvatar').textContent = iniciales;

        // Guardar datos para las gráficas
        appState.repruebasEstado = repruebasEstado;
        appState.garantiasMes = garantiasMes;
        appState.fallasMes = fallasMes;

    } catch (error) {
        console.error('Error cargando dashboard:', error);
    }
}

function openForgotPasswordModal(event) {
    if (event) event.preventDefault();
    document.getElementById('forgotPasswordModal').style.display = 'flex';
    document.getElementById('forgotPasswordEmail').value = '';
    document.getElementById('forgotPasswordMessage').style.display = 'none';
}

function closeForgotPasswordModal() {
    document.getElementById('forgotPasswordModal').style.display = 'none';
}

async function submitForgotPassword() {
    const email = document.getElementById('forgotPasswordEmail').value.trim();
    const msgDiv = document.getElementById('forgotPasswordMessage');

    if (!email) {
        msgDiv.textContent = '❌ Ingresa tu email';
        msgDiv.style.cssText = 'display:block; background:#f8d7da; color:#721c24; padding:10px; border-radius:6px;';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();
        msgDiv.textContent = '✅ Si el email está registrado recibirás un enlace en tu correo.';
        msgDiv.style.cssText = 'display:block; background:#d4edda; color:#155724; padding:10px; border-radius:6px;';
        document.getElementById('forgotPasswordEmail').value = '';
    } catch (error) {
        msgDiv.textContent = '❌ Error al enviar. Intenta de nuevo.';
        msgDiv.style.cssText = 'display:block; background:#f8d7da; color:#721c24; padding:10px; border-radius:6px;';
    }
}

// ==================== CARGA DATOS MAESTROS ====================

function initCargaDatosMaestros() {
    const section = document.getElementById('cargaDatosMaestrosSection');
    if (section && appState.rol === 'supervisor') {
        section.style.display = 'block';
    }

    const fileDanosPendientes = document.getElementById('fileDanosPendientes');
    const fileDanosCerrados = document.getElementById('fileDanosCerrados');

    if (fileDanosPendientes) {
        fileDanosPendientes.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('fileDanosPendientesNombre').textContent = file.name;
                document.getElementById('btnCargarDanosPendientes').style.display = 'inline-block';
            }
        });
    }

    if (fileDanosCerrados) {
        fileDanosCerrados.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('fileDanosCerradosNombre').textContent = file.name;
                document.getElementById('btnCargarDanosCerrados').style.display = 'inline-block';
            }
        });
    }
}

async function cargarDatosMaestros(tipo) {
    const config = {
        'danos-pendientes': {
            fileId: 'fileDanosPendientes',
            resultId: 'resultDanosPendientes',
            endpoint: `${API_BASE_URL}/repruebas/carga-danos-pendientes`
        },
        'danos-cerrados': {
            fileId: 'fileDanosCerrados',
            resultId: 'resultDanosCerrados',
            endpoint: `${API_BASE_URL}/repruebas/carga-danos-cerrados`
        }
    };

    const { fileId, resultId, endpoint } = config[tipo];
    const fileInput = document.getElementById(fileId);
    const resultDiv = document.getElementById(resultId);

    if (!fileInput.files[0]) {
        resultDiv.innerHTML = '<p style="color:#e74c3c;">❌ Selecciona un archivo primero</p>';
        return;
    }

    resultDiv.innerHTML = '<p style="color:#666;">⏳ Cargando...</p>';

    try {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { Authorization: `Bearer ${appState.token}` },
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            resultDiv.innerHTML = `<p style="color:#e74c3c;">❌ ${data.detail || 'Error al cargar'}</p>`;
            return;
        }

        resultDiv.innerHTML = `<p style="color:#27ae60;">✅ ${data.mensaje} — ${data.registros_insertados} registros insertados</p>`;
        fileInput.value = '';

    } catch (error) {
        resultDiv.innerHTML = `<p style="color:#e74c3c;">❌ Error de conexión</p>`;
    }
}