import discord
from discord import app_commands
from discord.ext import commands
import requests
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

# ================ CONFIGURAÇÃO ================
TOKEN_BOT = os.getenv("TOKEN_BOT")
CANAL_PROPAGANDA_ID = 1497722357660385381

# 🚨 DADOS NOVOS + PROXY BR PRA NÃO BLOQUEAR
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjE5ODc2NTQyMywicmVnaW9uX2NvZGUiOiJCUiIsImxhbmciOiJwdC1CUiIsImV4cCI6MTc2MDExNzYwMH0.3k9P2sR4vT7xW9zY8bA7cD5eF6gH7jI8kL9mM0nN1oP2qR3sT4uV5wX6yZ7"
COOKIE = "region=BR; lang=pt-BR; ssid=BR2026050210; open_id=198765423; access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9; device_sn=FFANDROID20260502"

# 🔌 PROXY BRASILEIRO - FAZ PARECER QUE É MEU CELULAR ACESSANDO
PROXIES = {
    "http": "http://177.128.122.234:8080",
    "https": "http://177.128.122.234:8080"
}

# 🇧🇷 ENDPOINTS NOVOS
URL_BASE = "https://service-restscape.garena.com/api/v1"
URL_LIKE = f"{URL_BASE}/interact/sendLike"
URL_CHECK = f"{URL_BASE}/player/checkPermission"

# 📝 HEADERS IGUAL MEU CELULAR
HEADERS = {
    "Host": "service-restscape.garena.com",
    "Connection": "keep-alive",
    "Accept": "application/json",
    "x-region-code": "BR",
    "x-language-code": "pt-BR",
    "x-client-version": "1.103.1",
    "x-device-model": "SM-G998B",
    "x-os-version": "Android 14",
    "User-Agent": "FreeFire/1.103.1 (Android 14; SM-G998B)",
    "Content-Type": "application/json; charset=utf-8",
    "Origin": "https://ff.garena.com",
    "Referer": "https://ff.garena.com/pt-br/",
    "Authorization": AUTH_TOKEN,
    "Cookie": COOKIE
}

# ==================================================

# CONFIGURAÇÕES
QUANTIDADE_FIXA = 200
LIMITE_DIARIO = 220
COOLDOWN_USER = 120
COOLDOWN_ID = 86400
MAX_TENTATIVAS = 5
DELAY = 0.05

# CONTROLE
user_cooldown = {}
id_cooldown = {}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")

# ✅ VERIFICAR CONEXÃO
def verificar_conexao():
    try:
        resp = requests.post(URL_CHECK, headers=HEADERS, json={}, timeout=8, proxies=PROXIES)
        return resp.status_code == 200
    except:
        return False

# ✅ ENVIAR LIKE
def enviar_like(id_alvo: str) -> bool:
    for _ in range(MAX_TENTATIVAS):
        try:
            payload = {
                "uid": str(id_alvo),
                "type": 1,
                "server_id": "BR",
                "timestamp": int(datetime.now().timestamp()*1000),
                "sign": "a1b2c3d4e5f6g7h8i9j0"
            }
            resp = requests.post(URL_LIKE, headers=HEADERS, json=payload, timeout=10, proxies=PROXIES)
            if resp.status_code == 200 and resp.json().get("code") == 0:
                return True
        except:
            pass
    return False

async def processar_pedido(id_alvo: str):
    sucessos = 0
    erros = 0
    inicio = datetime.now()

    for _ in range(QUANTIDADE_FIXA):
        if enviar_like(id_alvo):
            sucessos +=1
        else:
            erros +=1
        await asyncio.sleep(DELAY)

    tempo = round((datetime.now() - inicio).total_seconds(), 2)
    contabilizado = min(sucessos, LIMITE_DIARIO)
    return sucessos, erros, tempo, contabilizado

# ✅ PROPAGANDA
async def propaganda():
    canal = bot.get_channel(CANAL_PROPAGANDA_ID)
    if canal:
        await canal.send("""@everyone 🚀 **200 LIKES FREE FIRE BR | ENTREGA IMEDIATA** 🇧🇷

✅ Entrega em até 10 segundos
✅ Taxa de sucesso 99%+
✅ Sistema atualizado diariamente
✅ Suporte 24h

💸 **APENAS R$13,00**

👉 Use /like [ID] para pedir agora
🔥 MELHOR SERVIÇO DO MERCADO!
""")

# 📊 COMANDO STATUS
@bot.tree.command(name="status", description="Verificar sistema")
async def status(interaction: discord.Interaction):
    conectado = verificar_conexao()
    await interaction.response.send_message(f"""📊 STATUS DO SISTEMA
🤖 Sistema: {'✅ ONLINE' if conectado else '❌ OFFLINE'}
🔌 Conexão Garena: {'✅ FUNCIONANDO' if conectado else '❌ COM PROBLEMA'}
💛 Likes por pedido: {QUANTIDADE_FIXA}
⏱️ Tempo entrega: ~10s
""", ephemeral=True)

# 🎯 COMANDO PRINCIPAL
@bot.tree.command(name="like", description="Receber 200 likes")
@app_commands.describe(id="Digite o ID do jogador")
async def like(interaction: discord.Interaction, id: str):
    user_id = interaction.user.id
    agora = datetime.now()

    if not verificar_conexao():
        return await interaction.response.send_message("⚠️ Sistema em ajustes, tente novamente em 2 minutos!", ephemeral=True)

    if user_id in user_cooldown and (agora - user_cooldown[user_id]).total_seconds() < COOLDOWN_USER:
        tempo = round((COOLDOWN_USER - (agora - user_cooldown[user_id]).total_seconds())/60,1)
        return await interaction.response.send_message(f"⏳ Aguarde {tempo} minutos!", ephemeral=True)

    if id in id_cooldown and (agora - id_cooldown[id]).total_seconds() < COOLDOWN_ID:
        return await interaction.response.send_message("⚠️ Esse ID já recebeu likes hoje!", ephemeral=True)

    if not id.isdigit() or len(id) <8:
        return await interaction.response.send_message("❌ ID inválido, mínimo 8 números!", ephemeral=True)

    await interaction.response.defer()
    await interaction.followup.send(f"🔄 Processando pedido para ID: `{id}`... Aguarde ~10s!")

    sucessos, erros, tempo, contabilizado = await processar_pedido(id)

    user_cooldown[user_id] = agora
    id_cooldown[id] = agora

    await interaction.followup.send(f"""✅ ENTREGA FINALIZADA 🚀
🎯 ID: `{id}`
💛 Enviados: {sucessos}/{QUANTIDADE_FIXA}
✅ Contabilizados: {contabilizado}
❌ Falhas: {erros}
⏱️ Tempo: {tempo}s

💎 Volte sempre!
""")

# 🟢 INICIAR
@bot.event
async def on_ready():
    await bot.tree.sync()
    scheduler.add_job(propaganda, "interval", hours=2)
    scheduler.start()
    print(f"✅ BOT LIGADO | {bot.user} | COM PROXY BR ATIVADO")

bot.run(TOKEN_BOT)
        
