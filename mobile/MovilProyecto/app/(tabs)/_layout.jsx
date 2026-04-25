import { Tabs } from 'expo-router';
import UserProfileHeader from '../../components/UserProfileHeader';
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#714B67',
        tabBarInactiveTintColor: 'gray',
        headerShown: true,
        header: () => <UserProfileHeader />, 
      }}
    >
      <Tabs.Screen 
        name="index" 
        options={{
          title: 'Logs',
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons 
              name={focused ? 'list-circle' : 'list-circle-outline'} 
              size={size} 
              color={color} 
            />
          ),
        }} 
      />

      <Tabs.Screen
        name="notifications"
        options={{
          title: 'Notificaciones',
          tabBarBadge: 1,
          tabBarBadgeStyle: { backgroundColor: '#d9534f' },
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons 
              name={focused ? 'notifications' : 'notifications-outline'} 
              size={size} 
              color={color} 
            />
          ),
        }}
      />

      <Tabs.Screen
        name="validate_2fa"
        options={{
          href: null
        }}
      />
    </Tabs>
  );
}