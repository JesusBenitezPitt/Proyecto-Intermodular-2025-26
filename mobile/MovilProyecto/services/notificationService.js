import * as Notifications from 'expo-notifications';
import { saveTokenInOdoo } from './odooService';

export const registerPushNotifications = async (sessionId) => {
    try {
        const { status: existingStatus } = await Notifications.getPermissionsAsync();
        let finalStatus = existingStatus;
        
        if (existingStatus !== 'granted') {
            const { status } = await Notifications.requestPermissionsAsync();
            finalStatus = status;
        }

        if (finalStatus !== 'granted') {
            console.warn('Permiso de notificaciones denegado');
            return;
        }

        const tokenData = await Notifications.getExpoPushTokenAsync({
            projectId: 'da72762b-367c-4603-ab5a-9f2f44fb3a2e' 
        });
        const token = tokenData.data;

        const result = await saveTokenInOdoo(token, sessionId);
        console.log("Token vinculado en Odoo:", result);

        return token;
    } catch (error) {
        console.error("Error en proceso de notificaciones:", error);
    }
};