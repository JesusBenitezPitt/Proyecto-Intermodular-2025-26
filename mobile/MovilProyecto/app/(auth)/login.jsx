import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, Text, Alert, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { login } from '../../api/odoo'; // Importa la función que ya probamos

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert("Aviso", "Por favor, rellena todos los campos");
      return;
    }

    console.log("--- INICIANDO LOGIN ---");
    console.log("Credenciales:", email, "****");

    try {
      const res = await login(email, password);
      console.log("Respuesta cruda de Odoo:", JSON.stringify(res));

      if (res.result && res.result.status === 'success') {
        const { session_id, name } = res.result.data;
        console.log("Login exitoso. Usuario:", name);
        console.log("Guardando sesión...");

        await AsyncStorage.multiSet([
          ['session_id', session_id],
          ['user_name', name]
        ]);

        console.log("Sesión guardada. Intentando navegar a (tabs)...");
        
        // CAMBIO: Si /(tabs) falla, intenta solo '/' o '/(tabs)/index'
        router.replace('/(tabs)'); 
        
      } else {
        console.warn("Login fallido: Credenciales incorrectas o formato de respuesta inesperado");
        Alert.alert("Error", "Correo o contraseña incorrectos");
      }
    } catch (error) {
      console.error("--- ERROR CRÍTICO EN LOGIN ---");
      console.error("Mensaje:", error.message);
      console.error("Stack:", error.stack);
      Alert.alert("Error de conexión", "No se pudo conectar con el servidor Odoo");
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Seguridad Odoo</Text>
      <TextInput 
        placeholder="Correo electrónico" 
        value={email} 
        onChangeText={setEmail} 
        style={styles.input}
        autoCapitalize="none"
      />
      <TextInput 
        placeholder="Contraseña" 
        value={password} 
        onChangeText={setPassword} 
        secureTextEntry 
        style={styles.input}
      />
      <TouchableOpacity style={styles.button} onPress={handleLogin}>
        <Text style={styles.buttonText}>Iniciar Sesión</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 30, backgroundColor: '#fff' },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 30, textAlign: 'center', color: '#714B67' },
  input: { borderBottomWidth: 1, borderColor: '#ccc', marginBottom: 20, padding: 10, fontSize: 16 },
  button: { backgroundColor: '#714B67', padding: 15, borderRadius: 8, alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '600' }
});