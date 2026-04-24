import React, { useEffect, useState } from 'react';
import { View, Text, Image, TouchableOpacity, Alert, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function UserProfileHeader() {
  const [userData, setUserData] = useState({ name: '', photo: '' });
  const router = useRouter();

  useEffect(() => {
    const loadUserData = async () => {
      const name = await AsyncStorage.getItem('user_name');
      const photo = await AsyncStorage.getItem('user_photo');
      setUserData({ name: name || '', photo: photo || '' });
    };
    loadUserData();
  }, []);

  const handleLogoutPress = () => {
    Alert.alert("Cerrar Sesión", "¿Salir de la aplicación?", [
      { text: "Cancelar", style: "cancel" },
      { 
        text: "Salir", 
        style: "destructive", 
        onPress: async () => {
          await AsyncStorage.clear();
          router.replace('/(auth)/login');
        } 
      }
    ]);
  };

  const isSvgAvatar = userData.photo.startsWith('PD94bWw');
  const hasPhoto = userData.photo.length > 0;
  
  const userInitial = userData.name ? userData.name.charAt(0).toUpperCase() : '?';

  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <View style={styles.container}>
        <View style={styles.userInfo}>
          
          {hasPhoto && !isSvgAvatar ? (
            <Image 
              source={{ uri: `data:image/png;base64,${userData.photo}` }} 
              style={styles.avatar} 
            />
          ) : (
            <View style={[styles.avatar, styles.placeholder]}>
              <Text style={styles.initial}>{userInitial}</Text>
            </View>
          )}
          
          <Text style={styles.userName} numberOfLines={1}>
            {userData.name}
          </Text>
        </View>

        <TouchableOpacity onPress={handleLogoutPress} style={styles.settingsButton}>
          <Ionicons name="log-out-outline" size={24} color="#714B67" />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: '#fff', 
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 15,
    height: 60,
  },
  userInfo: { 
    flexDirection: 'row', 
    alignItems: 'center',
    flex: 1, 
  },
  avatar: { 
    width: 42, 
    height: 42, 
    borderRadius: 21,
    marginRight: 12 
  },
  placeholder: { 
    backgroundColor: '#714B67',
    justifyContent: 'center', 
    alignItems: 'center',
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
  },
  initial: { 
    color: '#fff', 
    fontWeight: 'bold',
    fontSize: 20,
    textTransform: 'toUpperCase',
  },
  userName: { 
    fontSize: 17, 
    fontWeight: '600', 
    color: '#333' 
  },
  settingsButton: { 
    padding: 8,
    marginLeft: 10 
  }
});