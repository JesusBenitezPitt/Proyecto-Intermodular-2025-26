import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Alert, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useOdoo } from '../../hooks/use-odoo';

export default function LogsScreen() {
  const [logs, setLogs] = useState([]);
  const { fetchLogs } = useOdoo();
  const router = useRouter();

  const loadData = async () => {
    try {
      const session = await AsyncStorage.getItem('session_id');
      if (!session) {
        router.replace('/(auth)/login');
        return;
      }
      const data = await fetchLogs(session);
      setLogs(data || []);
    } catch (error) {
      console.error("Error cargando logs:", error);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDecision = async (id, decision) => {
    Alert.alert("Acción realizada", `Has pulsado ${decision} para el log ${id}`);
  };

  const renderItem = ({ item }) => (
    <View style={[styles.card, item.riesgo === 'alto' && styles.alertCard]}>
      <View style={styles.headerRow}>
        <Text style={styles.fecha}>{item.fecha}</Text>
        <Text style={[styles.riesgoLabel, styles[item.riesgo]]}>
          {item.riesgo?.toUpperCase()}
        </Text>
      </View>
      
      <Text style={styles.usuario}>👤 {item.usuario}</Text>
      <Text style={styles.ip}>IP: {item.ip || '0.0.0.0'}</Text>

      <Text style={[styles.finalStatus, item.estado === 'exito' ? styles.verde : styles.rojo]}>
        Estado: {item.estado?.toUpperCase()}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={logs}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        contentContainerStyle={{ paddingBottom: 20 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f2f5', padding: 10 },
  card: { backgroundColor: '#fff', padding: 16, borderRadius: 12, marginBottom: 12, elevation: 4, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4 },
  alertCard: { borderLeftWidth: 6, borderLeftColor: '#ff4444' },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  fecha: { fontSize: 12, color: '#888' },
  usuario: { fontSize: 17, fontWeight: 'bold', color: '#333' },
  ip: { fontSize: 13, color: '#666', marginTop: 4 },
  riesgoLabel: { fontSize: 10, fontWeight: 'bold', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4, overflow: 'hidden' },
  bajo: { backgroundColor: '#e8f5e9', color: '#2e7d32' },
  medio: { backgroundColor: '#fff3e0', color: '#ef6c00' },
  alto: { backgroundColor: '#ffebee', color: '#c62828' },
  buttonContainer: { flexDirection: 'row', marginTop: 15, gap: 10 },
  btn: { flex: 1, padding: 10, borderRadius: 8, alignItems: 'center' },
  btnAccept: { backgroundColor: '#4CAF50' },
  btnDeny: { backgroundColor: '#F44336' },
  btnText: { color: '#fff', fontWeight: 'bold' },
  finalStatus: { marginTop: 10, textAlign: 'right', fontWeight: 'bold', fontSize: 12 },
  verde: { color: '#4CAF50' },
  rojo: { color: '#F44336' }
});