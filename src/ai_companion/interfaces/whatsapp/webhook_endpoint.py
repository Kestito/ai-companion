from fastapi import FastAPI
from ai_companion.interfaces.whatsapp.whatsapp_response import whatsapp_router

app = FastAPI()

# Update router prefix to use path-based routing
whatsapp_router.prefix = "/whatsapp"
app.include_router(whatsapp_router)
