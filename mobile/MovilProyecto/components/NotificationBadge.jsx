import { StyleSheet, Text, View } from 'react-native';

const NotificationBadge = ({ count }) => {
  if (!count || count <= 0) return null;

  const displayCount = count > 9 ? '+9' : count;

  return (
    <View style={styles.badge}>
      <Text style={styles.text}>{displayCount}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    position: 'absolute',
    right: -6,
    top: -3,
    backgroundColor: '#ff4444',
    borderRadius: 10,
    width: 18,
    height: 18,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#fff',
  },
  text: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
});

export default NotificationBadge;