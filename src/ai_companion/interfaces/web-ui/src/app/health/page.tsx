'use client';

import React, { useEffect, useState } from 'react';
import { Box, Container, Typography, Paper, Grid } from '@mui/material';
import { CheckCircle, Warning, Error } from '@mui/icons-material';

interface ServiceStatus {
  service: string;
  status: 'healthy' | 'degraded' | 'down';
  lastChecked: Date;
}

const statusIcons = {
  healthy: <CheckCircle color="success" />,
  degraded: <Warning color="warning" />,
  down: <Error color="error" />
};

export default function HealthPage() {
  const [statuses, setStatuses] = useState<ServiceStatus[]>([]);

  useEffect(() => {
    const checkServices = async () => {
      const services = [
        { 
          name: 'Python Backend', 
          check: async () => {
            try {
              const res = await fetch('/api/python/health');
              return res.ok ? 'healthy' : 'degraded';
            } catch {
              return 'down';
            }
          }
        },
        // Add other service checks here
      ];

      const results = await Promise.all(
        services.map(async (service) => ({
          service: service.name,
          status: await service.check() as 'healthy' | 'degraded' | 'down',
          lastChecked: new Date()
        }))
      );

      setStatuses(results);
    };

    checkServices();
    const interval = setInterval(checkServices, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        System Health Status
      </Typography>
      <Grid container spacing={3}>
        {statuses.map((status) => (
          <Grid item xs={12} sm={6} md={4} key={status.service}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                {statusIcons[status.status]}
                <Typography variant="h6" component="h2">
                  {status.service}
                </Typography>
              </Box>
              <Typography color="text.secondary" variant="body2">
                Status: {status.status}
              </Typography>
              <Typography color="text.secondary" variant="body2">
                Last checked: {status.lastChecked.toLocaleString()}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
} 