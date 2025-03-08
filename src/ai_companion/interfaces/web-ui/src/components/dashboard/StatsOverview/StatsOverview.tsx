import { Grid, Typography, Paper, SvgIcon } from '@mui/material'
import { MedicalIcon } from '@/components/icons/MedicalIcon'

interface StatsCardProps {
  title: string
  value: string | number
  icon?: React.ReactNode
}

const StatsCard = ({ title, value, icon }: StatsCardProps) => (
  <Paper sx={{ p: 2, textAlign: 'center', height: '100%' }}>
    {icon && <SvgIcon component={MedicalIcon} fontSize="large" color="primary" />}
    <Typography variant="h4" component="div" sx={{ mt: 1 }}>
      {value}
    </Typography>
    <Typography variant="body2" color="text.secondary">
      {title}
    </Typography>
  </Paper>
)

export const StatsOverview = () => {
  // In real implementation, fetch these from API
  const stats = {
    activeUsers: 148,
    newToday: 27,
    responseRate: 92
  }

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        <StatsCard 
          title="Active Users" 
          value={stats.activeUsers}
          icon={<MedicalIcon />}
        />
      </Grid>
      <Grid item xs={12} md={4}>
        <StatsCard 
          title="New Today" 
          value={stats.newToday}
        />
      </Grid>
      <Grid item xs={12} md={4}>
        <StatsCard 
          title="Response Rate" 
          value={`${stats.responseRate}%`}
        />
      </Grid>
    </Grid>
  )
}