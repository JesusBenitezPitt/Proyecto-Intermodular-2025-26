import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { respondToAuthRequest } from '../../services/odooService';

export default function Validate2FAScreen() {
  const { logId, notifId } = useLocalSearchParams();
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleDecision = async (decision) => {
    if (!notifId) return;

    setLoading(true);

    try {
      const result = await respondToAuthRequest(parseInt(notifId), decision);
      router.replace('/(tabs)');
    } catch (error) {
      console.error('Error al validar 2FA:', error);
      router.replace('/(tabs)');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>🔐 Verificación de Acceso</Text>
      <Text style={styles.subtitle}>
        Se ha detectado un intento de inicio de sesión.{'\n'}
        ¿Autorizas este acceso?
      </Text>

      {loading ? (
        <ActivityIndicator size="large" color="#714B67" />
      ) : (
        <>
          <TouchableOpacity
            style={[styles.button, styles.approveButton]}
            onPress={() => handleDecision('aproved')}
          >
            <Text style={styles.buttonText}>✓ Aprobar Acceso</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.denyButton]}
            onPress={() => handleDecision('denied')}
          >
            <Text style={styles.buttonText}>✗ Denegar y Bloquear</Text>
          </TouchableOpacity>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    justifyContent: 'center', 
    padding: 30, 
    backgroundColor: '#fff' 
  },
  title: { 
    fontSize: 28, 
    fontWeight: 'bold', 
    marginBottom: 20, 
    textAlign: 'center', 
    color: '#714B67' 
  },
  subtitle: { 
    fontSize: 16, 
    marginBottom: 40, 
    textAlign: 'center', 
    color: '#555',
    lineHeight: 24
  },
  button: { 
    padding: 18, 
    borderRadius: 10, 
    alignItems: 'center', 
    marginBottom: 15 
  },
  approveButton: { 
    backgroundColor: '#28a745' 
  },
  denyButton: { 
    backgroundColor: '#dc3545' 
  },
  buttonText: { 
    color: '#fff', 
    fontSize: 18, 
    fontWeight: '600' 
  },
  cancelButton: { 
    marginTop: 20, 
    alignItems: 'center' 
  },
  cancelText: { 
    color: '#714B67', 
    fontSize: 16 
  }
});