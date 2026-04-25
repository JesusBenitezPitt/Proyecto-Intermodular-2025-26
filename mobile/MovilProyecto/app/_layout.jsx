import { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, ActivityIndicator, Alert } from 'react-native';
import messaging from '@react-native-firebase/messaging';

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
    const unsubscribe = messaging().onNotificationOpenedApp(remoteMessage => {
      
      if (remoteMessage.data?.log_id) {
        router.push({
          pathname: '/notifications',
          params: { 
            logId: remoteMessage.data.log_id, 
            notifId: remoteMessage.data.notification_id 
          }
        });
      }
    });

    messaging()
      .getInitialNotification()
      .then(remoteMessage => {
        if (remoteMessage) {
          if (remoteMessage.data?.log_id) {
            setTimeout(() => {
              router.push({
                pathname: '/notifications',
                params: { 
                  logId: remoteMessage.data.log_id, 
                  notifId: remoteMessage.data.notification_id 
                }
              });
            }, 1000);
          }
        }
      });

    const unsubscribeForeground = messaging().onMessage(async remoteMessage => {
      Alert.alert(
        remoteMessage.notification?.title || 'Aviso de seguridad',
        remoteMessage.notification?.body || 'Nuevo inicio de sesión detectado',
        [
          { text: 'Ver detalles', onPress: () => router.push({
              pathname: '/notifications',
              params: { logId: remoteMessage.data.log_id }
          })},
          { text: 'Cerrar', style: 'cancel' }
        ]
      );
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
      <Stack.Screen 
        name="(auth)/login" 
        options={{ 
          headerShown: false 
        }} 
      />
      <Stack.Screen
        name="(tabs)" 
        options={{ 
          headerShown: false 
        }} 
      />
      <Stack.Screen 
        name="modal" 
        options={{ 
          presentation: 'modal'
        }} 
      />
    </Stack>
  );
}