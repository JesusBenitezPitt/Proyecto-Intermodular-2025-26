import messaging from '@react-native-firebase/messaging';
import { PermissionsAndroid, Platform } from 'react-native';
import { saveTokenInOdoo } from './odooService';

export const registerPushNotifications = async (sessionId) => {
    try {
        if (Platform.OS === 'android') {
            await PermissionsAndroid.request(
                PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS
            );
        }

        const authStatus = await messaging().requestPermission();
        const enabled =
            authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
            authStatus === messaging.AuthorizationStatus.PROVISIONAL;

        if (!enabled) {
            return;
        }

        const token = await messaging().getToken();
        
        console.log("FCM Token generado:", token);

        const result = await saveTokenInOdoo(token, sessionId);
        console.log("Token de Firebase vinculado en Odoo:", result);

        return token;
    } catch (error) {
        console.error("Error en proceso de notificaciones Firebase:", error);
    }
};