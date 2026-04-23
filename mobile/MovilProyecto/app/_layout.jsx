import { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, ActivityIndicator } from 'react-native';

export default function RootLayout() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    const checkLoginStatus = async () => {
      try {
        const sessionId = await AsyncStorage.getItem('session_id');
        setIsAuthenticated(!!sessionId);
      } catch (e) {
        setIsAuthenticated(false);
      } finally {
        setIsLoaded(true);
      }
    };
    checkLoginStatus();
  }, []);

  useEffect(() => {
    if (!isLoaded) return;

    // segments[0] nos dice en qué carpeta estamos
    const inAuthGroup = segments[0] === '(auth)';

    if (!isAuthenticated && !inAuthGroup) {
      // Si no tiene sesión y no está en login -> Al login
      router.replace('/(auth)/login');
    } else if (isAuthenticated && inAuthGroup) {
      // Si ya tiene sesión y está en login -> Al panel principal
      router.replace('/(tabs)');
    }
  }, [isAuthenticated, isLoaded, segments]);

  if (!isLoaded) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#714B67" /> 
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(auth)" />
      <Stack.Screen name="(tabs)" />
    </Stack>
  );
}