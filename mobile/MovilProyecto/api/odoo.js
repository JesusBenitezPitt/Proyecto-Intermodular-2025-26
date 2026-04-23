import AsyncStorage from '@react-native-async-storage/async-storage';
import { ODOO_CONFIG } from '../constants/config'; // Importamos la constante

export const login = async (login, password) => {
    try {
        const response = await fetch(`${ODOO_CONFIG.BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                params: { 
                    login, 
                    password, 
                    db: ODOO_CONFIG.DB // Usamos la DB de la constante
                }
            }),
        });
        return await response.json();
    } catch (error) {
        console.error("Error en login:", error);
        throw error;
    }
};

export const getLogs = async () => {
    try {
        const sessionId = await AsyncStorage.getItem('session_id');
        const response = await fetch(`${ODOO_CONFIG.BASE_URL}/api/security/logs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Cookie': `session_id=${sessionId}`
            },
            body: JSON.stringify({ params: {} }),
        });
        const data = await response.json();
        
        // Manejo de error por si la sesión expiró (error 100 que vimos antes)
        if (data.error && data.error.code === 100) {
            await AsyncStorage.removeItem('session_id');
            return null; 
        }

        return data.result.logs;
    } catch (error) {
        console.error("Error obteniendo logs:", error);
        return [];
    }
};