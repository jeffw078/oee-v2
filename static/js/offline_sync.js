class OfflineSyncManager {
    constructor() {
        this.dbName = 'oee_offline_db';
        this.dbVersion = 1;
        this.db = null;
        this.syncQueue = [];
        this.isOnline = navigator.onLine;
        this.lastSync = localStorage.getItem('last_sync') || null;
        
        this.init();
    }
    
    async init() {
        await this.initDB();
        this.setupEventListeners();
        this.startSyncInterval();
        this.updateConnectionStatus();
    }
    
    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Store para apontamentos offline
                if (!db.objectStoreNames.contains('apontamentos')) {
                    const store = db.createObjectStore('apontamentos', { keyPath: 'id', autoIncrement: true });
                    store.createIndex('timestamp', 'timestamp');
                    store.createIndex('sync_status', 'sync_status');
                }
                
                // Store para paradas offline
                if (!db.objectStoreNames.contains('paradas')) {
                    const store = db.createObjectStore('paradas', { keyPath: 'id', autoIncrement: true });
                    store.createIndex('timestamp', 'timestamp');
                    store.createIndex('sync_status', 'sync_status');
                }
                
                // Store para defeitos offline
                if (!db.objectStoreNames.contains('defeitos')) {
                    const store = db.createObjectStore('defeitos', { keyPath: 'id', autoIncrement: true });
                    store.createIndex('timestamp', 'timestamp');
                    store.createIndex('sync_status', 'sync_status');
                }
                
                // Store para cache de dados
                if (!db.objectStoreNames.contains('cache')) {
                    const store = db.createObjectStore('cache', { keyPath: 'key' });
                    store.createIndex('timestamp', 'timestamp');
                }
            };
        });
    }
    
    setupEventListeners() {
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
        
        // Interceptar formulários para salvar offline
        document.addEventListener('submit', (e) => this.handleFormSubmit(e));
    }
    
    handleOnline() {
        this.isOnline = true;
        this.updateConnectionStatus();
        this.syncOfflineData();
        this.showNotification('Conexão restaurada. Sincronizando dados...', 'success');
    }
    
    handleOffline() {
        this.isOnline = false;
        this.updateConnectionStatus();
        this.showNotification('Modo offline ativado. Dados serão sincronizados quando a conexão voltar.', 'warning');
    }
    
    updateConnectionStatus() {
        const statusElement = document.getElementById('status-conexao');
        if (statusElement) {
            statusElement.className = this.isOnline ? 'status-conexao' : 'status-conexao offline';
        }
    }
    
    async handleFormSubmit(event) {
        if (!this.isOnline) {
            event.preventDefault();
            
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            // Determinar tipo de dados baseado na action
            const action = form.action;
            let storeType = 'apontamentos';
            
            if (action.includes('parada')) {
                storeType = 'paradas';
            } else if (action.includes('defeito')) {
                storeType = 'defeitos';
            }
            
            // Salvar offline
            await this.saveOffline(storeType, {
                ...data,
                timestamp: new Date().toISOString(),
                sync_status: 'pending',
                form_action: action
            });
            
            this.showNotification('Dados salvos offline. Serão sincronizados quando a conexão voltar.', 'info');
        }
    }
    
    async saveOffline(storeType, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeType], 'readwrite');
            const store = transaction.objectStore(storeType);
            
            const request = store.add(data);
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
    
    async getOfflineData(storeType, status = 'pending') {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeType], 'readonly');
            const store = transaction.objectStore(storeType);
            const index = store.index('sync_status');
            
            const request = index.getAll(status);
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
    
    async syncOfflineData() {
        if (!this.isOnline) return;
        
        const stores = ['apontamentos', 'paradas', 'defeitos'];
        
        for (const store of stores) {
            const pendingData = await this.getOfflineData(store);
            
            for (const item of pendingData) {
                try {
                    await this.syncItem(store, item);
                    await this.markAsSynced(store, item.id);
                } catch (error) {
                    console.error(`Erro ao sincronizar ${store}:`, error);
                }
            }
        }
        
        this.lastSync = new Date().toISOString();
        localStorage.setItem('last_sync', this.lastSync);
        
        this.showNotification('Sincronização concluída com sucesso!', 'success');
    }
    
    async syncItem(storeType, item) {
        const response = await fetch(item.form_action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify(item)
        });
        
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }
        
        return response.json();
    }
    
    async markAsSynced(storeType, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeType], 'readwrite');
            const store = transaction.objectStore(storeType);
            
            const request = store.get(id);
            
            request.onsuccess = () => {
                const data = request.result;
                data.sync_status = 'synced';
                data.synced_at = new Date().toISOString();
                
                const updateRequest = store.put(data);
                updateRequest.onsuccess = () => resolve();
                updateRequest.onerror = () => reject(updateRequest.error);
            };
            
            request.onerror = () => reject(request.error);
        });
    }
    
    async cacheData(key, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cache'], 'readwrite');
            const store = transaction.objectStore('cache');
            
            const request = store.put({
                key: key,
                data: data,
                timestamp: new Date().toISOString()
            });
            
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }
    
    async getCachedData(key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cache'], 'readonly');
            const store = transaction.objectStore('cache');
            
            const request = store.get(key);
            
            request.onsuccess = () => {
                const result = request.result;
                resolve(result ? result.data : null);
            };
            
            request.onerror = () => reject(request.error);
        });
    }
    
    startSyncInterval() {
        // Tentar sincronizar a cada 2 minutos
        setInterval(() => {
            if (this.isOnline) {
                this.syncOfflineData();
            }
        }, 120000);
    }
    
    showNotification(message, type = 'info') {
        // Criar notificação visual
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.maxWidth = '400px';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Remover após 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    // Método público para fazer requisições com cache
    async makeRequest(url, options = {}) {
        const cacheKey = `${url}_${JSON.stringify(options)}`;
        
        if (!this.isOnline) {
            const cachedData = await this.getCachedData(cacheKey);
            if (cachedData) {
                return { ok: true, json: () => Promise.resolve(cachedData) };
            }
            throw new Error('Sem conexão e sem dados em cache');
        }
        
        try {
            const response = await fetch(url, options);
            
            if (response.ok) {
                const data = await response.json();
                await this.cacheData(cacheKey, data);
                return response;
            }
            
            return response;
        } catch (error) {
            this.isOnline = false;
            this.updateConnectionStatus();
            throw error;
        }
    }
}

// Inicializar sistema offline
document.addEventListener('DOMContentLoaded', function() {
    window.offlineSyncManager = new OfflineSyncManager();
});