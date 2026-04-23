import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';

export default function ProfileScreen() {
  const [name, setName] = useState('');
  const router = useRouter();

  useEffect(() => {
    const getUserData = async () => {
      const userName = await AsyncStorage.getItem('user_name');
      setName(userName || 'Usuario');
    };
    getUserData();
  }, []);

  const handleLogout = async () => {
    // 1. Limpiamos el almacenamiento
    await AsyncStorage.clear();
    // 2. Redirigimos al login (RootLayout detectará el cambio)
    router.replace('/(auth)/login');
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{name.charAt(0)}</Text>
        </View>
        <Text style={styles.welcome}>Hola, {name}</Text>
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Cerrar Sesión</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#fff', justifyContent: 'center' },
  header: { alignItems: 'center', marginBottom: 50 },
  avatar: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#714B67', justifyContent: 'center', alignItems: 'center', marginBottom: 15 },
  avatarText: { color: '#fff', fontSize: 32, fontWeight: 'bold' },
  welcome: { fontSize: 22, fontWeight: 'bold' },
  logoutButton: { backgroundColor: '#ff4444', padding: 15, borderRadius: 10, alignItems: 'center' },
  logoutText: { color: '#fff', fontWeight: 'bold', fontSize: 16 }
});