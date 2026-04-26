import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Alert, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { registerPushNotifications } from '../../services/notificationService';
import { login } from '../../services/odooService';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert("Aviso", "Por favor, rellena todos los campos");
      return;
    }

    try {
      const res = await login(email, password);

      if (res.result && res.result.status === 'success') {
        const { session_id, name, photo, log_id, notification_id } = res.result.data;

        await AsyncStorage.multiSet([
          ['session_id', session_id],
          ['user_name', name],
          ['user_photo', photo || '']
        ]);

        console.log("Login exitoso. Usuario:", name);

        if (log_id) {
          console.log("Acceso pendiente de validación 2FA");
          router.replace({
            pathname: '/validate_2fa',
            params: { logId: log_id, notifId: notification_id }
          });
        } else {
          router.replace('/(tabs)');
        }

        registerPushNotifications(session_id);
        
      } else {
        const errorMsg = res.result?.message || "Correo o contraseña incorrectos";
        Alert.alert("Acceso Denegado", errorMsg);
      }
    } catch (error) {
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
        keyboardType="email-address"
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