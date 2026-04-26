import { ODOO_CONFIG } from '../constants/config';

export const useOdoo = () => {
  const fetchLogs = async (sessionId) => {
    try {
      const response = await fetch(`${ODOO_CONFIG.BASE_URL}/api/security/logs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cookie': `session_id=${sessionId}`
        },
        body: JSON.stringify({ params: {} }),
      });
      const json = await response.json();
      return json.result.logs;
    } catch (error) {
      console.error("Error cargando logs:", error);
      return [];
    }
  };

  return { fetchLogs };
};