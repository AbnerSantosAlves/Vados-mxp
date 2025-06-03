
from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>MXP VADOS Bot - Status</title>
        <style>
            body { 
                background: #1a1a1a; 
                color: #00ffff; 
                font-family: 'Courier New', monospace; 
                text-align: center;
                padding: 50px;
            }
            h1 { color: #00ff00; }
            .status { color: #ffff00; }
            .cyber-box {
                border: 2px solid #00ffff;
                padding: 20px;
                margin: 20px auto;
                max-width: 600px;
                background: rgba(0, 255, 255, 0.1);
            }
        </style>
    </head>
    <body>
        <div class="cyber-box">
            <h1>🔰 MXP VADOS BOT</h1>
            <p class="status">STATUS: ONLINE ✅</p>
            <p>Madrid Futebol RP MXP</p>
            <p>Sistema de Recrutamento Ativo</p>
            <br>
            <p>📊 Bot está funcionando corretamente</p>
            <p>🚀 Keep Alive System Ativo</p>
        </div>
    </body>
    </html>
    """

@app.route('/status')
def status():
    return {"status": "online", "bot": "MXP VADOS", "system": "active"}

def run():
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print(f"🌐 Keep Alive server iniciado na porta {os.getenv('PORT', 5000)}")
