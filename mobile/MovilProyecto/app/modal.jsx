import { Link, Stack } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

export default function NotFoundScreen() {
  return (
    <>
      {/* Esto configura el título de la cabecera dinámicamente */}
      <Stack.Screen options={{ title: '¡Ups!' }} />
      
      <View style={styles.container}>
        <Text style={styles.title}>Esta pantalla no existe.</Text>
        
        <Link href="/" style={styles.link}>
          <Text style={styles.linkText}>Volver a la pantalla principal</Text>
        </Link>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  link: {
    marginTop: 15,
    paddingVertical: 15,
  },
  linkText: {
    fontSize: 14,
    color: '#2e78b7',
  },
});