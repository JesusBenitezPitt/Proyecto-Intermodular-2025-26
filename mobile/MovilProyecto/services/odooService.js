import AsyncStorage from '@react-native-async-storage/async-storage';
import { ODOO_CONFIG } from '../constants/config';

const fetchFromOdoo = async (endpoint, params = {}, useSession = true) => {
    const sessionId = useSession ? await AsyncStorage.getItem('session_id') : null;

    const headers = {
        'Content-Type': 'application/json',
    };

    if (sessionId) {
        headers['Cookie'] = `session_id=${sessionId}`;
        headers['X-Openerp-Session-Id'] = sessionId;
    };
    
    const response = await fetch(`${ODOO_CONFIG.BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: headers,
        credentials: 'include',
        body: JSON.stringify({ params }),
    });

    const data = await response.json();

    if (data.error && (data.error.code === 100 || data.error.data?.message === 'Session expired')) {
        await AsyncStorage.removeItem('session_id');
        return null;
    }
    return data;
};

export const login = async (login, password) => {
    return await fetchFromOdoo('/api/auth/login', {
        login,
        password,
        db: ODOO_CONFIG.DB
    }, false);
};

export const getLogs = async () => {
    const data = await fetchFromOdoo('/api/security/logs');
    return data?.result?.logs || [];
};

export const getNotifications = async () => {
    const data = await fetchFromOdoo('/api/security/notifications');
    return data?.result?.notifications || [];
};

export const markAsRead = async (notificationId) => {
    const data = await fetchFromOdoo('/api/security/notifications/read', {
        notification_id: notificationId
    });
    return data?.result?.status === 'success';
};

export const saveTokenInOdoo = async (token, sessionId) => {
    return await fetchFromOdoo('/api/security/register_token', { token }, true);
};

export const respondToAuthRequest = async (notificationId, decision) => {
    const data = await fetchFromOdoo('/api/security/validate_2fa', {
        notification_id: notificationId,
        decision: decision
    });
    return data?.result;
};

export const logoutFromOdoo = async () => {
    await fetchFromOdoo('/api/security/logout', {});
};