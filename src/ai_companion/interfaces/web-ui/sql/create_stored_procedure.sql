-- Create a stored procedure to get patient conversations including Telegram ones
CREATE OR REPLACE FUNCTION public.get_patient_conversations(p_patient_id UUID)
RETURNS SETOF conversations AS $$
BEGIN
  -- First get direct matches by patient_id
  RETURN QUERY
  SELECT * FROM public.conversations 
  WHERE patient_id = p_patient_id;
  
  -- Then try to find Telegram conversations by looking at patient metadata
  RETURN QUERY
  WITH patient_telegram AS (
    SELECT phone, email
    FROM public.patients
    WHERE id = p_patient_id
  )
  SELECT c.*
  FROM patient_telegram pt
  JOIN public.conversations c ON 
    (c.platform = 'telegram' AND 
     (
       -- Match by telegram ID in phone field
       (pt.phone LIKE 'telegram:%' AND 
        c.metadata::jsonb->>'telegram_id' = SUBSTRING(pt.phone FROM 10)) 
       OR
       -- Match by user_id in email JSON
       (pt.email::jsonb->>'user_id' IS NOT NULL AND 
        c.metadata::jsonb->>'telegram_id' = pt.email::jsonb->>'user_id')
     )
    );
END;
$$ LANGUAGE plpgsql; 