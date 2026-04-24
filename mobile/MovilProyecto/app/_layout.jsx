import { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, ActivityIndicator } from 'react-native';
// import * as Notifications from 'expo-notifications';

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
    /** 
     * const subscription = Notifications.addNotificationResponseReceivedListener(response => {
      const data = response.notification.request.content.data;
      
      if (data.log_id) {
        router.push({
          pathname: '/validate_2fa',
          params: { logId: data.log_id, notifId: data.notification_id }
        });
      }
    });

    return () => subscription.remove();
     */
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