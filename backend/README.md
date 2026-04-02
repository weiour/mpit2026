для запуска бэка
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

для запуска фронта
npm install
npm run dev

без ключей работать не будет 
.env:
SECRET_KEY=super-secret-key-change-me
ACCESS_TOKEN_EXPIRE_MINUTES=10080
VITE_API_URL=http://127.0.0.1:8000
GIGACHAT_CREDENTIALS=
GIGACHAT_CLIENT_ID=
GIGACHAT_CLIENT_SECRET=
GIGACHAT_VERIFY_SSL_CERTS=false
GIGACHAT_CA_BUNDLE_FILE=
GIGACHAT_MODEL=GigaChat
DGIS_API_KEY=
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CALENDAR_ID=kvn5331@gmail.com
GOOGLE_SERVICE_ACCOUNT_FILE=..\backend\service-account.json
GOOGLE_TIMEZONE=Europe/Moscow
SMTP_USER=kvn5331@gmail.com
SMTP_PASSWORD=sqkv qmql vcfx toif
EMAIL_FROM=kvn5331@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=true

service-account.json:
{
  "type": "service_account",
  "project_id": "",
  "private_key_id": "",
  "private_key": "",
  "client_email": "",
  "client_id": "",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "",
  "universe_domain": "googleapis.com"
}
