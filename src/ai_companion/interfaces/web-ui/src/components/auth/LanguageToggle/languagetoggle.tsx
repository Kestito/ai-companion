import { useTranslation } from 'react-i18next'
import { Button, ButtonGroup } from '@mui/material'

export const LanguageToggle = () => {
  const { i18n } = useTranslation()

  return (
    <ButtonGroup fullWidth variant="outlined" sx={{ mt: 2 }}>
      <Button 
        onClick={() => i18n.changeLanguage('lt')}
        disabled={i18n.language === 'lt'}
        aria-label="Lithuanian language"
      >
        🇱🇹 LT
      </Button>
      <Button
        onClick={() => i18n.changeLanguage('en')}
        disabled={i18n.language === 'en'}
        aria-label="English language"
      >
        🇬🇧 EN
      </Button>
    </ButtonGroup>
  )
}