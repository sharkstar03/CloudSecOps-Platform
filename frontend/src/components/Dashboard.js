import { useEffect, useState } from 'react';
import axios from 'axios';

const Dashboard = () => {
  const [data, setData] = useState({});

  useEffect(() => {
    axios.get('/api/scan/aws')
      .then(response => setData(response.data));
  }, []);

  return (
    <div>
      <h1>Cloud Security Dashboard</h1>
      {/* Visualización de datos */}
    </div>
  );
};

export default Dashboard;