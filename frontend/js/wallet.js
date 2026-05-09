// frontend/js/wallet.js
// Единый кошелёк и хранилище для всех страниц

const WALLET = {
    // ========== МОНЕТЫ ==========
    getCoins() {
        const wallet = JSON.parse(localStorage.getItem('wallet') || '{}');
        return wallet.coins || 0;
    },
    
    setCoins(amount) {
        const wallet = JSON.parse(localStorage.getItem('wallet') || '{}');
        wallet.coins = amount;
        localStorage.setItem('wallet', JSON.stringify(wallet));
        this.updateAllDisplays();
    },
    
    addCoins(amount) {
        this.setCoins(this.getCoins() + amount);
        this.syncToServer();
    },
    
    spendCoins(amount) {
        if (this.getCoins() >= amount) {
            this.setCoins(this.getCoins() - amount);
            this.syncToServer();
            return true;
        }
        return false;
    },
    
    updateAllDisplays() {
        document.querySelectorAll('.coin-display').forEach(el => {
            el.textContent = this.getCoins();
        });
    },

    // ========== АВАТАР ==========
    getAvatar() {
        const equipped = JSON.parse(localStorage.getItem('equipped') || '{}');
        return equipped.avatar || '';
    },
    
    setAvatar(avatar) {
        const equipped = JSON.parse(localStorage.getItem('equipped') || '{}');
        equipped.avatar = avatar;
        localStorage.setItem('equipped', JSON.stringify(equipped));
        this.syncToServer();
    },

    // ========== ПРЕДМЕТЫ ==========
    getOwnedItems() {
        return JSON.parse(localStorage.getItem('ownedItems') || '[]');
    },
    
    addOwnedItem(itemId) {
        const items = this.getOwnedItems();
        if (!items.includes(itemId)) {
            items.push(itemId);
            localStorage.setItem('ownedItems', JSON.stringify(items));
            this.syncToServer();
        }
    },
    
    hasItem(itemId) {
        return this.getOwnedItems().includes(itemId);
    },

    // ========== НАСТРОЙКИ ==========
    getSettings() {
        return JSON.parse(localStorage.getItem('settings') || '{}');
    },
    
    saveSettings(settings) {
        localStorage.setItem('settings', JSON.stringify(settings));
        this.syncToServer();
    },

    // ========== СИНХРОНИЗАЦИЯ С СЕРВЕРОМ ==========
    syncToServer() {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (!user.id) return;
        
        const equipped = JSON.parse(localStorage.getItem('equipped') || '{}');
        const ownedItems = this.getOwnedItems();
        const settings = this.getSettings();
        const wallet = JSON.parse(localStorage.getItem('wallet') || '{}');
        
        fetch('/api/user/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: user.id,
                coins: wallet.coins || 0,
                equipped: equipped,
                owned_items: ownedItems,
                settings: settings
            })
        }).catch(() => {});
    },
    
    loadFromServer() {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (!user.id) return;
        
        // Загружаем монеты
        fetch('/api/wallet', { headers: { 'X-User-Id': user.id } })
            .then(r => r.json())
            .then(data => {
                if (data.coins !== undefined) {
                    this.setCoins(data.coins);
                }
                if (data.avatar) {
                    const equipped = JSON.parse(localStorage.getItem('equipped') || '{}');
                    equipped.avatar = data.avatar;
                    localStorage.setItem('equipped', JSON.stringify(equipped));
                }
                if (data.owned_items) {
                    localStorage.setItem('ownedItems', JSON.stringify(data.owned_items));
                }
                if (data.settings) {
                    localStorage.setItem('settings', JSON.stringify(data.settings));
                }
            })
            .catch(() => {});
    }
};

// При загрузке страницы — загружаем с сервера
WALLET.loadFromServer();

// Каждые 30 секунд синхронизируем
setInterval(() => WALLET.syncToServer(), 30000);

// Сохраняем при закрытии страницы
window.addEventListener('beforeunload', () => {
    WALLET.syncToServer();
});