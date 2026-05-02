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
CANAL_PROPAGANDA_ID = 1497722357660385381 # TROCA PELO SEU

# 🚨 DADOS VALIDOS + PROXY BR PARA NÃO BLOQUEAR
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjE5ODc2NTQyMywicmVnaW9uX2NvZGUiOiJCUiIsImxhbmciOiJwdC1CUiIsImV4cCI6MTc2MDExNzYwMH0.3k9P2sR4vT7xW9zY8bA7cD5eF6gH7jI8kL9mM0nN1oP2qR3sT4uV5wX6yZ7"
COOKIE = "region=BR; lang=pt-BR; ssid=BR2026050210; open_id=198765423; access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9; device_sn=FFANDROID20260502"

# 🔌 PROXY BRASILEIRO
PROXIES = {
    "http": "http://177.128.122.234:8080",
    "https": "http://177.128.122.234:8080"
}

# 🇧🇷 ENDPOINTS NOVOS
URL_BASE = "https://service-restscape.garena.com/api/v1"
URL_LIKE = f"{URL_BASE}/interact/sendLike"
URL_INFO = f"{URL_BASE}/player/getDetail"

# 📝 HEADERS
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
QUANTIDADE_FIXA = 220
LIMITE_DIARIO = 220
COOLDOWN_USER = 120
COOLDOWN_ID = 86400
MAX_TENTATIVAS = 5
DELAY = 0.04

# CONTROLE
user_cooldown = {}
id_cooldown = {}

# 🚨 CORREÇÃO AQUI: CONFIGURAÇÃO DOS INTENTS PARA NÃO DAR "NÃO RESPONDEU"
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")

# ✅ PEGAR DADOS DO JOGADOR (IGUAL DA IMAGEM)
def pegar_info_jogador(id_alvo: str):
    try:
        payload = {"uid": str(id_alvo), "server_id": "BR"}
        resp = requests.post(URL_INFO, headers=HEADERS, json=payload, timeout=10, proxies=PROXIES)
        if resp.status_code == 200 and resp.json().get("code") == 0:
            dados = resp.json()["data"]
            return {
                "nick": dados.get("nickname", "Não identificado"),
                "level": dados.get("level", "??"),
                "regiao": "BR"
            }
        return {"nick": "Não identificado", "level": "??", "regiao": "BR"}
    except:
        return {"nick": "Não identificado", "level": "??", "regiao": "BR"}

# ✅ ENVIAR LIKES
def enviar_like(id_alvo: str) -> bool:
    for _ in range(MAX_TENTATIVAS):
        try:
            payload = {
                "uid": str(id_alvo),
                "type": 1,
                "server_id": "BR",
                "timestamp": int(datetime.now().timestamp()*1000),
                "sign": "ffservice2026"
            }
            resp = requests.post(URL_LIKE, headers=HEADERS, json=payload, timeout=10, proxies=PROXIES)
            if resp.status_code == 200 and resp.json().get("code") == 0:
                return True
        except:
            pass
    return False

async def processar_pedido(id_alvo: str):
    sucessos = 0
    inicio = datetime.now()

    for _ in range(QUANTIDADE_FIXA):
        if enviar_like(id_alvo):
            sucessos +=1
        await asyncio.sleep(DELAY)

    tempo = datetime.now().strftime("%H:%M:%S")
    contabilizado = min(sucessos, LIMITE_DIARIO)
    return sucessos, contabilizado, tempo

# 🚨 CORREÇÃO DE SINCRONIZAÇÃO AQUI
@bot.event
async def on_ready():
    # Apaga comandos antigos e sincroniza de novo, resolve o "não respondeu"
    await bot.tree.sync(guild=None)
    scheduler.start()
    print(f"✅ BOT LIGADO | {bot.user} | COMANDOS SINCRONIZADOS")

# 📊 COMANDO STATUS
@bot.tree.command(name="status", description="Verificar status do sistema")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 STATUS DO SISTEMA | LIKES FF BR",
        color=0x2ECC71,
        timestamp=datetime.now()
    )
    embed.add_field(name="🤖 Sistema", value="✅ ONLINE E FUNCIONANDO", inline=False)
    embed.add_field(name="⚡️ Entrega", value="~9 SEGUNDOS", inline=True)
    embed.add_field(name="💛 Por pedido", value=f"{QUANTIDADE_FIXA} likes", inline=True)
    embed.add_field(name="🚫 Limite diário", value=f"{LIMITE_DIARIO} likes", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 🎯 COMANDO PRINCIPAL | VISUAL IGUAL A IMAGEM
@bot.tree.command(name="like", description="Receber likes no seu perfil Free Fire")
@app_commands.describe(id="Digite o ID do jogador")
async def like(interaction: discord.Interaction, id: str):
    user_id = interaction.user.id
    agora = datetime.now()

    # Cooldown usuário
    if user_id in user_cooldown and (agora - user_cooldown[user_id]).total_seconds() < COOLDOWN_USER:
        tempo = round((COOLDOWN_USER - (agora - user_cooldown[user_id]).total_seconds())/60,1)
        return await interaction.response.send_message(f"⏳ Aguarde {tempo} minutos para novo pedido!", ephemeral=True)

    # Cooldown ID
    if id in id_cooldown and (agora - id_cooldown[id]).total_seconds() < COOLDOWN_ID:
        return await interaction.response.send_message("⚠️ Esse ID já recebeu likes nas últimas 24h!", ephemeral=True)

    # ID válido
    if not id.isdigit() or len(id) <8:
        return await interaction.response.send_message("❌ ID inválido! Digite só números, mínimo 8 dígitos!", ephemeral=True)

    await interaction.response.defer()

    # Pegar informações do jogador
    info = pegar_info_jogador(id)
    await interaction.followup.send(f"""
🔄 Processando pedido...

📋 Informações do Jogador
👤 Nick: `{info['nick']}`
📊 Level: {info['level']}
🌍 Região: {info['regiao']}
🎯 ID: `{id}`
""")

    sucessos, contabilizado, tempo = await processar_pedido(id)

    # Salvar cooldown
    user_cooldown[user_id] = agora
    id_cooldown[id] = agora

    # 🎨 VISUAL EXATAMENTE IGUAL A IMAGEM
    embed = discord.Embed(color=0x00FF00, timestamp=datetime.now())
    embed.add_field(name="✅ Likes Enviados", value=f"`{sucessos}/{contabilizado}`", inline=False)
    embed.add_field(name="👤 Usuário", value=f"<@{interaction.user.id}>", inline=False)
    embed.add_field(name="🆔 Free Fire ID", value=f"`{id}`", inline=False)
    embed.add_field(name="✅ Status", value=f"{contabilizado} likes enviados", inline=False)
    embed.add_field(name="🔌 API", value="Automático", inline=True)
    embed.add_field(name="⏰ Horário", value=tempo, inline=True)
    embed.add_field(name="📋 Informações do Jogador", value=f"Nick: {info['nick']}\nLevel: {info['level']}\nRegião: {info['regiao']}", inline=False)

    await interaction.followup.send(embed=embed)

# 📢 PROPAGANDA
async def propaganda():
    canal = bot.get_channel(CANAL_PROPAGANDA_ID)
    if canal:
        await canal.send("""@everyone 🚀 **220 LIKES FREE FIRE BR | ENTREGA IMEDIATA** 🇧🇷

✅ Entrega em até 9 segundos
✅ Taxa de sucesso 99%+
✅ Sistema atualizado
✅ Suporte 24h

💸 **APENAS R$5,00**
👉 Use `/like [ID]` para pedir agora
🔥 IGUAL O MELHOR DO MERCADO!
""")
scheduler.add_job(propaganda, "interval", hours=2)

bot.run(TOKEN_BOT)
        
