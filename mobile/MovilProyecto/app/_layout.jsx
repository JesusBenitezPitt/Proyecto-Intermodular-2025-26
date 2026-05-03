import AsyncStorage from '@react-native-async-storage/async-storage';
import messaging from '@react-native-firebase/messaging';
import { Stack, useRouter, useSegments } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';

export default function RootLayout() {
  const [isLoaded, setIsLoaded] = useState(false);
  const segments = useSegments();
  const router = useRouter();

  const checkAuth = async () => {
    const sessionId = await AsyncStorage.getItem('session_id');
    const inAuthGroup = segments[0] === '(auth)';

    if (!sessionId && !inAuthGroup) {
      router.replace('/(auth)/login');
    } else if (sessionId && inAuthGroup) {
      router.replace('/(tabs)');
    }
    
    if (!isLoaded) setIsLoaded(true);
  };

  useEffect(() => {
    checkAuth();
  }, [segments]);

  useEffect(() => {
    // Notificación cuando la app está en background y se abre
    const unsubscribe = messaging().onNotificationOpenedApp(remoteMessage => {
      console.log('Notificación abierta desde background:', remoteMessage);
      
      if (remoteMessage.data?.requires_action === 'true') {
        router.push({
          pathname: '/validate_2fa',
          params: { 
            logId: remoteMessage.data.log_id, 
            notifId: remoteMessage.data.notification_id 
          }
        });
      } else if (remoteMessage.data?.log_id) {
        router.push('/notifications');
      }
    });

    // Notificación cuando la app estaba cerrada completamente
    messaging()
      .getInitialNotification()
      .then(remoteMessage => {
        if (remoteMessage) {
          console.log('App abierta desde notificación (cerrada):', remoteMessage);
          
          setTimeout(() => {
            if (remoteMessage.data?.requires_action === 'true') {
              router.push({
                pathname: '/validate_2fa',
                params: { 
                  logId: remoteMessage.data.log_id, 
                  notifId: remoteMessage.data.notification_id 
                }
              });
            } else if (remoteMessage.data?.log_id) {
              router.push('/notifications');
            }
          }, 1000);
        }
      });

    // Notificación cuando la app está en foreground (abierta)
    const unsubscribeForeground = messaging().onMessage(async remoteMessage => {
      console.log('Notificación recibida en foreground:', remoteMessage);

      if (remoteMessage.data?.requires_action === 'true') {
        router.push({
          pathname: '/validate_2fa',
          params: {
            logId: remoteMessage.data.log_id,
            notifId: remoteMessage.data.notification_id
          }
        });
      } else {
        router.push('/notifications');
      }
    });

    return () => {
      unsubscribe();
      unsubscribeForeground();
    };
  }, []);

  if (!isLoaded) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#714B67" /> 
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(auth)/login" />
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="modal" options={{ presentation: 'modal' }} />
    </Stack>
  );
}