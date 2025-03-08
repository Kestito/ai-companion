import { List, ListItem, ListItemText, Typography, Paper } from '@mui/material'
import ScheduleIcon from '@mui/icons-material/Schedule'

interface ActivityItem {
  timestamp: string
  user: string
  action: string
  platform: 'telegram' | 'whatsapp'
}

export const ActivityTimeline = () => {
  const activities: ActivityItem[] = [
    {
      timestamp: '2023-08-16T15:42:00',
      user: 'J. Smith',
      action: 'Medication reminder',
      platform: 'whatsapp'
    },
    {
      timestamp: '2023-08-16T15:30:00',
      user: 'A. Jonaitis',
      action: 'Message sent',
      platform: 'telegram'
    }
  ]

  return (
    <Paper sx={{ p: 2, mt: 2 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <ScheduleIcon sx={{ mr: 1 }} /> Recent Activity
      </Typography>
      <List dense>
        {activities.map((activity, index) => (
          <ListItem key={index} sx={{ py: 0.5 }}>
            <ListItemText
              primary={`${new Date(activity.timestamp).toLocaleTimeString()} • ${activity.user}`}
              secondary={`${activity.action} (${activity.platform})`}
              primaryTypographyProps={{ variant: 'body2' }}
              secondaryTypographyProps={{ variant: 'caption' }}
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  )
}