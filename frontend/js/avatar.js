// frontend/js/avatar.js
// Локальное хранилище аватаров (IndexedDB)

const AvatarCache = {
    DB_NAME: 'igrishe_avatars',
    STORE_NAME: 'avatars',
    
    // Открыть базу
    async openDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.DB_NAME, 1);
            request.onupgradeneeded = () => {
                request.result.createObjectStore(this.STORE_NAME);
            };
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    },
    
    // Сохранить аватар в кэш
    async save(userId, file) {
        const db = await this.openDB();
        const tx = db.transaction(this.STORE_NAME, 'readwrite');
        tx.objectStore(this.STORE_NAME).put(file, 'user_' + userId);
        return tx.complete;
    },
    
    // Загрузить аватар из кэша
    async load(userId) {
        const db = await this.openDB();
        const tx = db.transaction(this.STORE_NAME, 'readonly');
        const file = await tx.objectStore(this.STORE_NAME).get('user_' + userId);
        return file || null;
    },
    
    // Конвертировать File в base64 строку
    fileToBase64(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.readAsDataURL(file);
        });
    },
    
    // Применить аватар ко всем элементам на странице
    applyToAll(base64) {
        document.querySelectorAll('.profile-avatar, .avatar-big').forEach(el => {
            if (el.tagName === 'IMG') {
                el.src = base64;
            } else {
                el.innerHTML = `<img src="${base64}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`;
            }
        });
    }
};