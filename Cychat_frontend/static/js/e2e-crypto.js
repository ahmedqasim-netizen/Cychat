const E2ECrypto = (function() {
    'use strict';

    const PRIVATE_KEY_STORAGE = 'e2e_private_key';
    const PUBLIC_KEY_STORAGE = 'e2e_public_key';
    const ROOM_KEYS_STORAGE = 'e2e_room_keys';


    const ECDH_ALGORITHM = { name: 'ECDH', namedCurve: 'P-256' };
    const AES_ALGORITHM = { name: 'AES-GCM', length: 256 };


    let cachedKeyPair = null;
    const derivedKeysCache = new Map();
    const roomKeysCache = new Map();



    function arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    function base64ToArrayBuffer(base64) {
        try {
            const binary = atob(base64);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {
                bytes[i] = binary.charCodeAt(i);
            }
            return bytes.buffer;
        } catch (e) {
            console.error('base64ToArrayBuffer error:', e);
            throw new Error('Invalid base64 string');
        }
    }



    async function generateKeyPair() {
        return await window.crypto.subtle.generateKey(
            ECDH_ALGORITHM,
            true,
            ['deriveKey', 'deriveBits']
        );
    }

    async function exportPublicKey(publicKey) {
        const exported = await window.crypto.subtle.exportKey('spki', publicKey);
        return arrayBufferToBase64(exported);
    }

    async function exportPrivateKey(privateKey) {
        const exported = await window.crypto.subtle.exportKey('pkcs8', privateKey);
        return arrayBufferToBase64(exported);
    }

    async function importPublicKey(base64Key) {
        const keyData = base64ToArrayBuffer(base64Key);
        return await window.crypto.subtle.importKey(
            'spki',
            keyData,
            ECDH_ALGORITHM,
            true,
            []
        );
    }

    async function importPrivateKey(base64Key) {
        const keyData = base64ToArrayBuffer(base64Key);
        return await window.crypto.subtle.importKey(
            'pkcs8',
            keyData,
            ECDH_ALGORITHM,
            true,
            ['deriveKey', 'deriveBits']
        );
    }

    async function storeKeyPair(keyPair) {
        const privateKeyBase64 = await exportPrivateKey(keyPair.privateKey);
        const publicKeyBase64 = await exportPublicKey(keyPair.publicKey);
        localStorage.setItem(PRIVATE_KEY_STORAGE, privateKeyBase64);
        localStorage.setItem(PUBLIC_KEY_STORAGE, publicKeyBase64);
        cachedKeyPair = keyPair;
    }

    async function loadKeyPair() {
        if (cachedKeyPair) return cachedKeyPair;

        const privateKeyBase64 = localStorage.getItem(PRIVATE_KEY_STORAGE);
        const publicKeyBase64 = localStorage.getItem(PUBLIC_KEY_STORAGE);

        if (!privateKeyBase64 || !publicKeyBase64) return null;

        try {
            const privateKey = await importPrivateKey(privateKeyBase64);
            const publicKey = await importPublicKey(publicKeyBase64);
            cachedKeyPair = { privateKey, publicKey };
            return cachedKeyPair;
        } catch (e) {
            console.error('Error loading key pair:', e);
            return null;
        }
    }

    function hasKeys() {
        return localStorage.getItem(PRIVATE_KEY_STORAGE) !== null &&
               localStorage.getItem(PUBLIC_KEY_STORAGE) !== null;
    }

    function getStoredPublicKey() {
        return localStorage.getItem(PUBLIC_KEY_STORAGE);
    }

    function clearKeys() {
        localStorage.removeItem(PRIVATE_KEY_STORAGE);
        localStorage.removeItem(PUBLIC_KEY_STORAGE);
        localStorage.removeItem(ROOM_KEYS_STORAGE);
        cachedKeyPair = null;
        derivedKeysCache.clear();
        roomKeysCache.clear();
    }



    async function deriveSharedKey(privateKey, publicKey) {
        return await window.crypto.subtle.deriveKey(
            { name: 'ECDH', public: publicKey },
            privateKey,
            AES_ALGORITHM,
            false,
            ['encrypt', 'decrypt']
        );
    }

    async function getSharedKey(theirPublicKeyBase64, cacheKey) {
        if (cacheKey && derivedKeysCache.has(cacheKey)) {
            return derivedKeysCache.get(cacheKey);
        }

        const keyPair = await loadKeyPair();
        if (!keyPair) {
            throw new Error('No local keys found');
        }

        const theirPublicKey = await importPublicKey(theirPublicKeyBase64);
        const sharedKey = await deriveSharedKey(keyPair.privateKey, theirPublicKey);

        if (cacheKey) {
            derivedKeysCache.set(cacheKey, sharedKey);
        }

        return sharedKey;
    }

    function clearDerivedKey(cacheKey) {
        derivedKeysCache.delete(cacheKey);
    }

    function clearAllDerivedKeys() {
        derivedKeysCache.clear();
    }



    async function encryptMessage(plaintext, key) {
        const encoder = new TextEncoder();
        const data = encoder.encode(plaintext);
        const iv = window.crypto.getRandomValues(new Uint8Array(12));

        const encrypted = await window.crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv },
            key,
            data
        );


        const combined = new Uint8Array(iv.length + encrypted.byteLength);
        combined.set(iv);
        combined.set(new Uint8Array(encrypted), iv.length);

        return arrayBufferToBase64(combined.buffer);
    }

    async function decryptMessage(ciphertextBase64, key) {
        const combined = new Uint8Array(base64ToArrayBuffer(ciphertextBase64));
        const iv = combined.slice(0, 12);
        const ciphertext = combined.slice(12);

        const decrypted = await window.crypto.subtle.decrypt(
            { name: 'AES-GCM', iv: iv },
            key,
            ciphertext
        );

        const decoder = new TextDecoder();
        return decoder.decode(decrypted);
    }


    async function encryptFor(message, recipientPublicKeyBase64, cacheKey) {
        if (!recipientPublicKeyBase64) {
            throw new Error('Recipient public key is required');
        }
        const sharedKey = await getSharedKey(recipientPublicKeyBase64, cacheKey);
        return await encryptMessage(message, sharedKey);
    }

    async function decryptFrom(ciphertextBase64, senderPublicKeyBase64, cacheKey) {
        if (!senderPublicKeyBase64) {
            throw new Error('Sender public key is required');
        }
        if (!ciphertextBase64) {
            throw new Error('Ciphertext is required');
        }
        const sharedKey = await getSharedKey(senderPublicKeyBase64, cacheKey);
        return await decryptMessage(ciphertextBase64, sharedKey);
    }


    async function initialize() {
        let keyPair = await loadKeyPair();
        let isNew = false;

        if (!keyPair) {
            console.log('Generating new E2E keys...');
            keyPair = await generateKeyPair();
            await storeKeyPair(keyPair);
            isNew = true;
        }

        const publicKeyBase64 = await exportPublicKey(keyPair.publicKey);
        return { publicKey: publicKeyBase64, isNew };
    }


    async function generateRoomKey() {
        return await window.crypto.subtle.generateKey(
            AES_ALGORITHM,
            true,
            ['encrypt', 'decrypt']
        );
    }

    async function exportRoomKey(roomKey) {
        const exported = await window.crypto.subtle.exportKey('raw', roomKey);
        return arrayBufferToBase64(exported);
    }

    async function importRoomKey(base64Key) {
        const keyData = base64ToArrayBuffer(base64Key);
        return await window.crypto.subtle.importKey(
            'raw',
            keyData,
            AES_ALGORITHM,
            true,
            ['encrypt', 'decrypt']
        );
    }

    async function storeRoomKey(roomName, roomKey) {
        roomKeysCache.set(roomName, roomKey);
        try {
            const roomKeyBase64 = await exportRoomKey(roomKey);
            const stored = JSON.parse(localStorage.getItem(ROOM_KEYS_STORAGE) || '{}');
            stored[roomName] = roomKeyBase64;
            localStorage.setItem(ROOM_KEYS_STORAGE, JSON.stringify(stored));
        } catch (e) {
            console.error('Error storing room key:', e);
        }
    }

    async function getRoomKey(roomName) {
        if (roomKeysCache.has(roomName)) {
            return roomKeysCache.get(roomName);
        }

        try {
            const stored = JSON.parse(localStorage.getItem(ROOM_KEYS_STORAGE) || '{}');
            if (stored[roomName]) {
                const roomKey = await importRoomKey(stored[roomName]);
                roomKeysCache.set(roomName, roomKey);
                return roomKey;
            }
        } catch (e) {
            console.error('Error loading room key:', e);
        }

        return null;
    }

    function getRoomKeyBase64(roomName) {
        try {
            const stored = JSON.parse(localStorage.getItem(ROOM_KEYS_STORAGE) || '{}');
            return stored[roomName] || null;
        } catch (e) {
            return null;
        }
    }

    function hasRoomKey(roomName) {
        if (roomKeysCache.has(roomName)) return true;
        try {
            const stored = JSON.parse(localStorage.getItem(ROOM_KEYS_STORAGE) || '{}');
            return !!stored[roomName];
        } catch (e) {
            return false;
        }
    }

    function clearRoomKey(roomName) {
        roomKeysCache.delete(roomName);
        try {
            const stored = JSON.parse(localStorage.getItem(ROOM_KEYS_STORAGE) || '{}');
            delete stored[roomName];
            localStorage.setItem(ROOM_KEYS_STORAGE, JSON.stringify(stored));
        } catch (e) {
            console.error('Error clearing room key:', e);
        }
    }

    function clearAllRoomKeys() {
        roomKeysCache.clear();
        localStorage.removeItem(ROOM_KEYS_STORAGE);
    }

    async function encryptForRoom(message, roomName) {
        const roomKey = await getRoomKey(roomName);
        if (!roomKey) {
            throw new Error('No room key for: ' + roomName);
        }
        return await encryptMessage(message, roomKey);
    }

    async function decryptFromRoom(ciphertextBase64, roomName) {
        const roomKey = await getRoomKey(roomName);
        if (!roomKey) {
            throw new Error('No room key for: ' + roomName);
        }
        return await decryptMessage(ciphertextBase64, roomKey);
    }

    async function encryptRoomKeyForUser(roomKeyBase64, userPublicKeyBase64) {
        const keyPair = await loadKeyPair();
        if (!keyPair) throw new Error('No local keys');

        const userPublicKey = await importPublicKey(userPublicKeyBase64);
        const sharedKey = await deriveSharedKey(keyPair.privateKey, userPublicKey);

        const encoder = new TextEncoder();
        const data = encoder.encode(roomKeyBase64);
        const iv = window.crypto.getRandomValues(new Uint8Array(12));

        const encrypted = await window.crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv },
            sharedKey,
            data
        );

        const combined = new Uint8Array(iv.length + encrypted.byteLength);
        combined.set(iv);
        combined.set(new Uint8Array(encrypted), iv.length);

        return arrayBufferToBase64(combined.buffer);
    }

    async function decryptRoomKey(encryptedRoomKeyBase64, senderPublicKeyBase64) {
        const keyPair = await loadKeyPair();
        if (!keyPair) throw new Error('No local keys');

        const senderPublicKey = await importPublicKey(senderPublicKeyBase64);
        const sharedKey = await deriveSharedKey(keyPair.privateKey, senderPublicKey);

        const combined = new Uint8Array(base64ToArrayBuffer(encryptedRoomKeyBase64));
        const iv = combined.slice(0, 12);
        const ciphertext = combined.slice(12);

        const decrypted = await window.crypto.subtle.decrypt(
            { name: 'AES-GCM', iv: iv },
            sharedKey,
            ciphertext
        );

        const decoder = new TextDecoder();
        return decoder.decode(decrypted);
    }


    async function generateFingerprint(publicKeyBase64) {
        const keyData = base64ToArrayBuffer(publicKeyBase64);
        const hash = await window.crypto.subtle.digest('SHA-256', keyData);
        const hashArray = Array.from(new Uint8Array(hash));
        return hashArray.slice(0, 8).map(b => b.toString(16).padStart(2, '0')).join(':').toUpperCase();
    }


    async function selfTest() {
        console.log('=== E2ECrypto Self Test ===');
        try {
            const alice = await generateKeyPair();
            const bob = await generateKeyPair();

            const alicePub = await exportPublicKey(alice.publicKey);
            const bobPub = await exportPublicKey(bob.publicKey);

            const aliceShared = await deriveSharedKey(alice.privateKey, await importPublicKey(bobPub));
            const message = 'Test message ' + Date.now();
            const encrypted = await encryptMessage(message, aliceShared);

            const bobShared = await deriveSharedKey(bob.privateKey, await importPublicKey(alicePub));
            const decrypted = await decryptMessage(encrypted, bobShared);

            if (decrypted === message) {
                console.log('✓ SELF TEST PASSED');
                return true;
            } else {
                console.error('✗ SELF TEST FAILED: Message mismatch');
                return false;
            }
        } catch (error) {
            console.error('✗ SELF TEST FAILED:', error);
            return false;
        }
    }

    function debugState() {
        return {
            hasKeys: hasKeys(),
            publicKey: getStoredPublicKey()?.substring(0, 50),
            derivedKeysCount: derivedKeysCache.size,
            roomKeysCount: roomKeysCache.size
        };
    }

    return {
        initialize,
        hasKeys,
        clearKeys,
        getStoredPublicKey,
        loadKeyPair,
        exportPublicKey,
        importPublicKey,
        encryptFor,
        decryptFrom,
        encryptMessage,
        decryptMessage,
        getSharedKey,
        clearDerivedKey,
        clearAllDerivedKeys,
        generateFingerprint,
        generateRoomKey,
        exportRoomKey,
        importRoomKey,
        encryptRoomKeyForUser,
        decryptRoomKey,
        storeRoomKey,
        getRoomKey,
        getRoomKeyBase64,
        hasRoomKey,
        clearRoomKey,
        clearAllRoomKeys,
        encryptForRoom,
        decryptFromRoom,
        selfTest,
        debugState
    };
})();


if (typeof module !== 'undefined' && module.exports) {
    module.exports = E2ECrypto;
}
