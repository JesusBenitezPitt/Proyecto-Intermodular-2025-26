import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { getLogDetails, respondToAuthRequest } from '../../services/odooService';
import { Ionicons } from '@expo/vector-icons';

export default function Validate2FAScreen() {
  const { logId, notifId } = useLocalSearchParams();
  const [log, setLog] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    loadLogInfo();
  }, [logId]);

  const loadLogInfo = async () => {
    try {
      const data = await getLogDetails(logId);
      setLog(data);
    } catch (error) {
      Alert.alert("Error", "No se pudo obtener la información del intento de acceso.");
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision) => {
    const actionText = decision === 'aprobado' ? "autorizar" : "bloquear";
    
    Alert.alert(
      "Confirmar",
      `¿Estás seguro de que deseas ${actionText} este acceso?`,
      [
        { text: "Cancelar", style: "cancel" },
        { 
          text: "Confirmar", 
          onPress: async () => {
            setLoading(true);
            const res = await respondToAuthRequest(notifId, decision);
            if (res.status === 'success' || res.status === 'blocked') {
              router.replace('/(tabs)');
            }
            setLoading(false);
          }
        }
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#714B67" />
        <Text style={styles.loadingText}>Verificando seguridad...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Ionicons name="shield-checkmark" size={80} color="#714B67" />
        <Text style={styles.title}>Solicitud de Acceso</Text>
        <Text style={styles.subtitle}>Se ha detectado un inicio de sesión en tu cuenta de Odoo.</Text>
      </View>

      <View style={styles.card}>
        <DetailRow icon="globe-outline" label="IP" value={log?.ip} />
        <DetailRow icon="navigate-outline" label="Ubicación" value={log?.localizacion} />
        <DetailRow icon="desktop-outline" label="Navegador" value={log?.navegador} />
        <DetailRow 
            icon="alert-circle-outline" 
            label="Riesgo IA" 
            value={log?.nivel_riesgo?.toUpperCase()} 
            color={log?.nivel_riesgo === 'alto' ? '#dc3545' : '#ffc107'}
        />
      </View>

      <View style={styles.footer}>
        <TouchableOpacity 
          style={[styles.btn, styles.btnApprove]} 
          onPress={() => handleDecision('aprobado')}
        >
          <Text style={styles.btnText}>SÍ, SOY YO</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.btn, styles.btnDeny]} 
          onPress={() => handleDecision('denegado')}
        >
          <Text style={styles.btnText}>NO, BLOQUEAR MI CUENTA</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const DetailRow = ({ icon, label, value, color = '#333' }) => (
  <View style={styles.row}>
    <Ionicons name={icon} size={20} color="#666" style={{ width: 30 }} />
    <Text style={styles.label}>{label}:</Text>
    <Text style={[styles.value, { color }]}>{value}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff', padding: 25 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { alignItems: 'center', marginTop: 40, marginBottom: 30 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#333', marginTop: 10 },
  subtitle: { fontSize: 14, color: '#666', textAlign: 'center', marginTop: 5 },
  card: { backgroundColor: '#f9f9f9', borderRadius: 15, padding: 20, marginBottom: 30, elevation: 2 },
  row: { flexDirection: 'row', marginBottom: 15, alignItems: 'center' },
  label: { fontSize: 14, color: '#888', width: 80 },
  value: { fontSize: 14, fontWeight: '600', flex: 1 },
  footer: { marginTop: 'auto', marginBottom: 20 },
  btn: { paddingVertical: 15, borderRadius: 12, alignItems: 'center', marginBottom: 15 },
  btnApprove: { backgroundColor: '#714B67' }, // Tu color corporativo
  btnDeny: { backgroundColor: '#fff', borderWidth: 2, borderColor: '#dc3545' },
  btnText: { fontWeight: 'bold', fontSize: 16, color: '#fff' },
  loadingText: { marginTop: 10, color: '#714B67' }
});

styles.btnTextDeny = { ...styles.btnText, color: '#dc3545' }; 