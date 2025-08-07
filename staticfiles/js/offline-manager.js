// arquivo: static/js/offline-manager.js (NOVO)

class OfflineManager {
    constructor() {
        this.dbName = 'OEE_Offline_DB';
        this.storeName = 'apontamentos_offline';
        this.db = null;
        this.syncInterval = null;
        
        this.initDB();
        this.setupEventListeners();
        this.startSyncInterval();
    }
    
    // Inicializar IndexedDB
    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, 1);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                if (!db.objectStoreNames.contains(this.storeName)) {
                    const store = db.createObjectStore(this.storeName, { 
                        keyPath: 'id', 
                        autoIncrement: true 
                    });
                    store.createIndex('tipo', 'tipo', { unique: false });
                    store.createIndex('sincronizado', 'sincronizado', { unique: false });
                    store.createIndex('timestamp', 'timestamp', { unique: false });
                }
            };
        });
    }
    
    // Salvar dados offline
    async salvarOffline(tipo, dados) {
        const transaction = this.db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        
        const registro = {
            tipo: tipo,
            dados: dados,
            timestamp: new Date().toISOString(),
            sincronizado: false,
            tentativas: 0
        };
        
        return new Promise((resolve, reject) => {
            const request = store.add(registro);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
    
    // continuação do arquivo: static/js/offline-manager.js

    // Buscar dados não sincronizados
    async buscarNaoSincronizados() {
        const transaction = this.db.transaction([this.storeName], 'readonly');
        const store = transaction.objectStore(this.storeName);
        const index = store.index('sincronizado');
        
        return new Promise((resolve, reject) => {
            const request = index.getAll(false);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
    
    // Marcar como sincronizado
    async marcarSincronizado(id) {
        const transaction = this.db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        
        const request = store.get(id);
        request.onsuccess = () => {
            const registro = request.result;
            registro.sincronizado = true;
            registro.dataSync = new Date().toISOString();
            store.put(registro);
        };
    }
    
    // Sincronizar com servidor
    async sincronizarComServidor() {
        if (!navigator.onLine) {
            console.log('Sem conexão - sincronização adiada');
            return;
        }
        
        try {
            const naoSincronizados = await this.buscarNaoSincronizados();
            
            if (naoSincronizados.length === 0) {
                console.log('Nada para sincronizar');
                return;
            }
            
            console.log(`Sincronizando ${naoSincronizados.length} registros...`);
            
            for (const registro of naoSincronizados) {
                try {
                    const response = await fetch('/soldagem/api/sync_offline/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            tipo: registro.tipo,
                            dados: registro.dados,
                            timestamp_offline: registro.timestamp
                        })
                    });
                    
                    if (response.ok) {
                        await this.marcarSincronizado(registro.id);
                        this.mostrarNotificacao('Dados sincronizados!', 'success');
                    } else {
                        registro.tentativas++;
                        if (registro.tentativas > 5) {
                            console.error('Máximo de tentativas excedido:', registro);
                        }
                    }
                } catch (error) {
                    console.error('Erro ao sincronizar registro:', error);
                }
            }
        } catch (error) {
            console.error('Erro na sincronização:', error);
        }
    }
    
    // Configurar event listeners
    setupEventListeners() {
        // Detectar mudanças de conexão
        window.addEventListener('online', () => {
            console.log('Conexão restaurada - iniciando sincronização');
            this.atualizarStatusConexao(true);
            this.sincronizarComServidor();
        });
        
        window.addEventListener('offline', () => {
            console.log('Conexão perdida - modo offline ativado');
            this.atualizarStatusConexao(false);
        });
        
        // Interceptar submissões de formulário
        document.addEventListener('submit', async (e) => {
            if (e.target.dataset.offline === 'true') {
                e.preventDefault();
                await this.handleFormOffline(e.target);
            }
        });
    }
    
    // Lidar com formulário offline
    async handleFormOffline(form) {
        const formData = new FormData(form);
        const dados = Object.fromEntries(formData);
        const tipo = form.dataset.tipo || 'form';
        
        if (!navigator.onLine) {
            // Salvar offline
            await this.salvarOffline(tipo, dados);
            this.mostrarNotificacao('Dados salvos localmente!', 'warning');
            
            // Limpar formulário
            form.reset();
            
            // Redirecionar se necessário
            if (form.dataset.redirect) {
                window.location.href = form.dataset.redirect;
            }
        } else {
            // Enviar normalmente
            form.submit();
        }
    }
    
    // Iniciar intervalo de sincronização
    startSyncInterval() {
        // Tentar sincronizar a cada 30 segundos
        this.syncInterval = setInterval(() => {
            if (navigator.onLine) {
                this.sincronizarComServidor();
            }
        }, 30000);
    }
    
    // Atualizar indicador visual
    atualizarStatusConexao(online) {
        const indicadores = document.querySelectorAll('.status-conexao');
        
        indicadores.forEach(el => {
            if (online) {
                el.classList.remove('status-offline');
                el.classList.add('status-online');
                el.querySelector('.status-text').textContent = 'Online';
            } else {
                el.classList.remove('status-online');
                el.classList.add('status-offline');
                el.querySelector('.status-text').textContent = 'Offline';
            }
        });
    }
    
    // Mostrar notificação
    mostrarNotificacao(mensagem, tipo = 'info') {
        // Criar elemento de notificação
        const notif = document.createElement('div');
        notif.className = `notificacao notificacao-${tipo}`;
        notif.innerHTML = `
            <div class="notificacao-conteudo">
                <span>${mensagem}</span>
                <button onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Adicionar ao body
        document.body.appendChild(notif);
        
        // Remover após 5 segundos
        setTimeout(() => {
            notif.remove();
        }, 5000);
    }
    
    // Obter cookie CSRF
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Cache de componentes para uso offline
    async cacheComponentes() {
        try {
            const response = await fetch('/soldagem/api/componentes/');
            const componentes = await response.json();
            localStorage.setItem('componentes_cache', JSON.stringify(componentes));
        } catch (error) {
            console.error('Erro ao cachear componentes:', error);
        }
    }
    
    // Obter componentes (online ou cache)
    async getComponentes() {
        if (navigator.onLine) {
            await this.cacheComponentes();
            return JSON.parse(localStorage.getItem('componentes_cache') || '[]');
        } else {
            return JSON.parse(localStorage.getItem('componentes_cache') || '[]');
        }
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.offlineManager = new OfflineManager();
});