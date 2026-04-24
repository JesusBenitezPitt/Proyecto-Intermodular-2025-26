import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, RefreshControl, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { getNotifications, markAsRead } from '../../services/odooService';

export default function ScreenNotifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Función para cargar los datos
  const fetchNotifications = async () => {
    try {
      const data = await getNotifications();
      setNotifications(data || []);
    } catch (error) {
      console.error("Error al cargar notificaciones:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Cargar al montar el componente
  useEffect(() => {
    fetchNotifications();
  }, []);

  // Función para cuando el usuario desliza hacia abajo para refrescar
  const onRefresh = () => {
    setRefreshing(true);
    fetchNotifications();
  };

  // Función para marcar como leída al tocar la notificación
  const handlePress = async (id, isRead) => {
    if (!isRead) {
      const success = await markAsRead(id);
      if (success) {
        // Actualizamos el estado local para que se vea el cambio sin recargar todo
        setNotifications(prev => 
          prev.map(n => n.id === id ? { ...n, leida: true } : n)
        );
      }
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, { justifyContent: 'center' }]}>
        <ActivityIndicator size="large" color="#714B67" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={notifications}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <Text style={styles.emptyText}>No tienes notificaciones pendientes.</Text>
        }
        renderItem={({ item }) => (
          <TouchableOpacity 
            style={[styles.card, item.leida && styles.cardRead]} 
            onPress={() => handlePress(item.id, item.leida)}
          >
            <View style={styles.iconContainer}>
              <Ionicons 
                name={item.tipo === 'warning' || item.tipo === 'danger' ? "warning" : "notifications"} 
                size={24} 
                color={item.leida ? "#999" : (item.tipo === 'warning' ? "#FFA500" : "#714B67")} 
              />
            </View>
            <View style={styles.textContainer}>
              <Text style={[styles.title, item.leida && styles.textRead]}>{item.titulo}</Text>
              <Text style={styles.message}>{item.mensaje}</Text>
              <Text style={styles.time}>{item.fecha}</Text>
            </View>
            {!item.leida && <View style={styles.unreadDot} />}
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9f9f9' },
  card: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 15,
    marginVertical: 8,
    marginHorizontal: 16,
    borderRadius: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    alignItems: 'center'
  },
  cardRead: {
    backgroundColor: '#f1f1f1',
    elevation: 0,
    opacity: 0.8
  },
  unreadDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#714B67',
    marginLeft: 5
  },
  iconContainer: { justifyContent: 'center', marginRight: 15 },
  textContainer: { flex: 1 },
  title: { fontSize: 16, fontWeight: 'bold', color: '#333' },
  textRead: { color: '#888', fontWeight: 'normal' },
  message: { fontSize: 14, color: '#666', marginVertical: 4 },
  time: { fontSize: 12, color: '#999' },
  emptyText: { textAlign: 'center', marginTop: 50, color: '#999', fontSize: 16 }
});